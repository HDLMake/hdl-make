#!/bin/bash
#script should be run by make

##$1 is expected to be project path
if [ $# -lt 1 ]; then
	echo "$0"': Argument expected'
	echo "Usage: $0 project_path hdl_path"
	exit 1
fi

if [ ! -d $1 ]; then
	echo "$0"':'"$1"'is not a directory'
	echo "Usage: $0 project_path hdl_path"
	exit 1
fi
hdl_path=$1
scripts_path=$2
##modules file is obligatory for each simulation
if [ ! -f $(pwd)/modules ]; then
	echo "$0: Modules file does not exist"
	echo "Do not know what modules are necessary for current testbench"
	echo "Exiting"
	exit 1
fi

modules=$(cat $(pwd)/modules)

vhdl_srcs=""

for module in $modules; do
	module_path=$hdl_path"/"$module
	if [ ! -d $module_path ]; then
		echo "Module directory $module_path does not exists"
		echo "Exiting"
		exit 1
	fi
	
	cd $module_path
	if [ -f "./manifest" -o -f "./Manifest" ]; then
		##manifest is specified
		#echo "Manifest file for $module found" >&2
		final_vhdl_src=""
		
		parity=0
		manifest_files=$(cat ./manifest | awk -f $scripts_path/manifest.awk --assign pwd_=$(pwd))
		for file in $manifest_files; do
			if [ $parity -eq 1 ]; then
					printf " "
			fi 
			
			parity=$(($parity+1))
			printf $file
			
			if [ $parity -eq 2 ]; then
				printf "\n"
				parity=0
			fi
		done
	else
		#echo "Manifest file not found for $module" >&2
		#echo "Using all files from module $module" >&2
	
		temp=$(ls *.vhd 2>/dev/null)
		for i in $temp; do
			echo $(pwd)"/$i work"
		done
	fi	
done

#echo "$vhdl_srcs"

