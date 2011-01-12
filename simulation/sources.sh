#!/bin/bash
#script should be run by make

function usage() {
	echo "Usage: $0 hdl_path scripts_path"
}
##$1 is expected to be project path
if [ $# -ne 2 ]; then
	echo "$0"': two arguments expected'
	usage
	exit 1
fi

if [ ! -d $1 ]; then
	echo "$0"':'"$1"'is not a directory'
	usage
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
			
			
			if [ $parity -eq 1 ]; then
				printf '%s\n' "$file"
			else
				parity=0
			fi
		done
	else
		#echo "Manifest file not found for $module" >&2
		#echo "Using all files from module $module" >&2
	
		temp=$(ls *.vhd 2>/dev/null)
		for i in $temp; do
			echo $(pwd)"/$i"
		done
	fi	
done
