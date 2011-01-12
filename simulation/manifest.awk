#script for scanning manifest file
#files with full path are output
#in output there is file's full path and its library
#for instance: /path/to/project/hdl/module/file	work

#example:

BEGIN{
	#pwd_ should be passed as launch argument
	vhdl_src = "";
}
{
	if( $0 ~ /^#.*$/ || $0 ~ /^\s*$/ )
		; #skip
	else {
		if(NF == 2) { #library is specified
			vhdl_src = vhdl_src " " pwd_ "/" $1 " " $2
		}
		else
		if(NF == 1) { #default library (work)
			vhdl_src = vhdl_src " " pwd_ "/" $1 " work"
		}
	}
}
END{
	vhdl_src = substr(vhdl_src,2,length(vhdl_src));
	print vhdl_src;
}
function chop_last(path) {
	new_path = gensub(/(.*?)\/(.*)/, "\\1", "g", path);
	return new_path;
}
