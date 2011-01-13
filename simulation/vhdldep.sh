#!/bin/bash
#script should be run by make

function abs_path() {
	local cur_dir=$(pwd)
	local D=$(dirname $1)
	local B=$(basename $1)
	(cd $D && echo $(pwd)"/$B") || exit 1 
	cd $cur_dir
}

##associative array declaration
if [ $# -lt 2 ]; then
	echo "$0"': Argument expected'
	echo "Usage: $0 project_path compilation_instr"
	exit 1
fi

if [ ! -d "$1" ]; then
	echo "$0: folder $1 does not exist"
	echo "Usage: $0 project_path compilation_inst"
	exit 1
fi

scripts_path=$(abs_path $1)
vhd_comp=$2

number=0
declare -a files
declare -a libs
declare -A libs_dict
while read a b; do #data is given in the form "file library"
	files[$number]="$a";
	libs[$number]="$b";
	all_files="$all_files $a"
	all_libs="$all_libs $b"
	libs_dict[$b]=${libs_dict[$b]}" "$a
	number=$(($number+1))
done

for i in $(seq 0 $(($number-1))); do ##for each source file

	precedent_files=$(cat ${files[$i]} | awk -f $scripts_path/precedence.awk)
	basename=$(basename ${files[$i]})
	dirname=$(dirname ${files[$i]})
	corename=$(echo $basename| awk '{print gensub(/([^.]*)\.vhd/, "\\1", "g", $0);}')

	obj="$obj $(pwd)/${libs[$i]}/$corename/_primary.dat"
	echo "$(pwd)/${libs[$i]}/$corename/_primary.dat: ${files[$i]}"
	echo "	$vhd_comp -work ${libs[$i]} ${files[$i]} " #\\"
	#echo "|| rm -rf $(pwd)/${libs[$i]}/$corename" ## <-- in the original version this line was included, but now I don't know what it is for
	echo ""
	#printf '%s' "${files[$i]}:$precedent_files"  
	if [ -n "$precedent_files" ]; then
		printf '%s' "$(pwd)/${libs[$i]}/$corename/_primary.dat:"
		for file in $precedent_files; do	
			prec_file=$(echo $file|awk '{n=split($0,t,".");print t[2]}')
			prec_lib=$(echo $file|awk '{n=split($0,t,".");print t[1]}')
			if [ -z "${libs_dict[$prec_lib]}" ]; then
				echo "Library $prec_lib from file $file is not listed in modules' manifest files" >&2
				echo "Exiting" >&2
				exit 1
			fi
			printf ' \\\n%s' "$(pwd)/$prec_lib/$prec_file/_primary.dat"
			prec_file_full_path=$(echo ${libs_dict[$prec_lib]} | awk '{for(i=1; i<=NF; ++i) {print $i;}}' - | grep $prec_file -)
			if [ $? -ne 0 ]; then
				echo "File $prec_file.vhd required by '${files[$i]}' is not found within used modules or its library is wrong" >&2 
				echo "Exiting" >&2
				exit 1
			fi
			#printf ' \\\n%s' $prec_file_full_path;
		done
		echo ""
		echo ""
	fi
done
uniq_libs=$(echo $all_libs | tr " " "\n" | sort -u | tr "\n" " ")
#for lib in $uniq_libs; do
#	uniq_libs_long="$uniq_libs_long $(pwd)/$lib"
#done
echo ''
echo 'VHDL_OBJ:='"$obj"
echo ''
echo 'LIBS:='"$uniq_libs"
echo 'LIB_IND:='$(echo $uniq_libs | tr " " "\n" | awk '{print $0 "/." $0}' | tr "\n" " ")
#echo 'LIBS:'
for lib in $uniq_libs; do
	printf '%s\n\t%s\n\t%s\n' "$lib/.$lib:" "(vlib $lib && vmap -modelsimini $(pwd)/modelsim.ini $lib $(pwd)/$lib) || rm -r $lib" "touch $lib/.$lib" 
done
