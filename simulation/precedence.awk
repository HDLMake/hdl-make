#the script looks for "use" statements in files \
#that are given as input argument \
#if "use" does not concern standard library,
#then name of precedent file is printed

BEGIN {
	std_libs[0]="ieee";
	std_libs[1]="altera_mf";
	std_libs[2]="cycloneiii";
	std_libs[3]="lpm";
	std_libs[4]="std";
	#std_libs[5]="wbgen2";
	depend="";
}
{
	if( $0 ~ /^[ \t]*use[ \t]+[^ ]+\s*/) {
		number = split($2,tokens,".");
		std=0;
		#get rid of semicolon
		if(tokens[number] ~ /[^;]*;/)
			tokens[number]=substr(tokens[number],1,length(tokens[number])-1);
		for(ind in std_libs) {
			if(std_libs[ind]==tolower(tokens[1])) {
				std=1;
				break;
			}
		}
		if(std == 0)
		#	if(tokens[1] == "work")
				print tokens[1] "." tokens[2];
		#	else {
		#		for(i=1; i<= number; ++i)
		#			depend = depend"."tokens[i];
		#		depend=substr(depend,2,length(depend))
		#		print depend
		#		depend=""
		#	}
				
	}
}
END {
	#depend = substr(depend,2,length(depend)); #chop last <space>
	#print depend;
}
