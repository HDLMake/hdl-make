#!/bin/bash

########################################################################################
# Variables for modification. 

# data for logging in via ssh
R_MACHINE="localhost"
R_USER="pawel"
ARCH_NAME="arch.tar"
########################################################################################
#  The following variables are set automatically by the script.
#+ If you believe that the script won't set them properly
#+ then change appropriate variables.Otherwise leave it as it is.

declare prj_file="" #.prj file is required by the xflow tool. It is to be generated with ISE.
declare ise_proj_file="" #main ise project file. Its extension should be either .ise or .xise

# The following line is intended to automatically detect the design name
#+If it doesn't work replace it with the actual name
design_name=$(ls | grep -e '^.*\.xise' | sed -e 's/\(.*\)\.xise/\1/g')

SYNTHESIS_COMMAND="xflow -p xc6slx150t-2-fgg676 -implement balanced -config bitgen $design_name"
########################################################################################
# DO NOT MODIFY BELOW THIS POINT -> .
########################################################################################

function message() {
	#local PURPLE="\033[35m"
	#local NORMAL="\033[m"
	echo -e "$PURPLE""$1""$NORMAL" >&2
}
function abs_path() {
	local cur_dir=$(pwd)
	local D=$(dirname $1)
	local B=$(basename $1)
	(cd $D && echo $(pwd)"/$B") || exit 1 
	cd $cur_dir
}
function abs_path_list() {
	local ret=""
	if [ $# -gt 1 ]; then
		 while [ $# -gt 0 ]; do
			ret="$ret "`abs_path $1`
			shift
		done
		echo $ret
		return
	else 
		if [ $# -eq 1 ]; then
			for i in $1; do
				ret="$ret "`abs_path $i`
			done
		fi
		echo $ret
		return
	fi
}
#function usage() {
#	echo "Usage: $0 project_path"
#	echo "Exiting"
#	exit 1
#}
function escape() {
	echo $1 | sed 's/(/\\\(/g; s/)/\\\)/g'
}

#path to programs as constants 
SYNPLIFY=""
XTCLSH=""
IMPACT=""


proj_path=$(abs_path $(pwd))
proj_path=${proj_path%/}
proj_path=${proj_path%.}

#check if the variable was specified by the user
if [ "x$ise_proj_file" = "x" ]; then
	ise_proj_file=$(ls $proj_path | grep -e '.*\.xise$' )
	#check if there is exactle one project file in the specified catalogue
	if [ $(echo $ise_proj_file | wc -w) -ne 1 ]; then
		cat <<-EOH
			Inpropriate number of ISE project files
			Project file (.xise) must be passed
			as the second argument by script call
	EOH
		exit 1
	fi
fi
ise_proj_file=$(abs_path $ise_proj_file)

#check if the variable was specified by the user
if [ "x$syn_proj_file" = "x" ]; then
	prj_file=$(ls $proj_path | grep -e '.*\.prj$')
	if [ $(echo $prj_file | wc -w) -ne 1 ]; then
		cat <<-EOH
			Inpropriate number of Synplify project files
			Project file (.prj) must be passed
			as the third argument by script call
	EOH
		exit 1
	fi
fi
syn_proj_file=$(abs_path $syn_proj_file)

#check if there is 'extra-files' or 'Extra-files' in the current catalogue
extra_files=""
if [ ! -e 'extra-files' ]; then
	if [ ! -e 'Extra-files' ]; then
		echo 'No extra-files listing found' >&2
		echo 'Assuming there are no extra file for synthesis' >&2
	else
		echo 'Extra-files listing found' >&2
		echo 'Taking it into account' >&2
		extra_files=$(cat Extra-files)	
	fi
else 
	if [ ! -e 'Extra-files' ]; then
		echo 'extra-files listing found' >&2
		echo 'Taking it into account' >&2
		extra_files=$(cat extra-files)
	else
		echo 'Both extra-files and Extra-files listing found' >&2
		echo 'Taking the former into account' >&2
		extra_files=$(cat extra-files)
	fi
fi

# create a random string for a new remote catalogue
temp=$(date | md5sum | md5sum )
randstring="${temp:2:10}"

#extract vhdl filenames from .xise project file 
vhdl_files=$(awk '{ if($0 ~ /<file .*>/) {print gensub(/.*<file .*name="([^"]*)".*>/, "\\1", "g");} }' $ise_proj_file)

# convert vhdl files names to their absulte paths
vhdl_files=$(abs_path_list $vhdl_files)

# convert extra-files' names to their absolute path
extra_files=$(abs_path_list $extra_files)

#make list of all files that will be transfered
transfered_files="$vhdl_files $extra_files $syn_proj_file $ise_proj_file $xsvf_gen_file $xtclsh_file $mcs_gen_file"
message "Creating synthesis director named $randstring on the remote machine..." &&
ssh $R_USER@$R_MACHINE "mkdir -p $randstring" &&
message "Transferring vhdl files, project files and scripts to remote machine..." &&
tar -cvjf - $transfered_files | ssh $R_USER@$R_MACHINE "(cd $randstring; tar xjf -)" &&

message "Running synthesis and fitting on $R_MACHINE..." &&
ssh $R_USER@$R_MACHINE $SYNTHESIS_COMMAND &&

#check for new files, put them in an archive and transfer back
message "Creating list of files that should be copied back..." &&
back_files=$(
	ssh $R_USER@$R_MACHINE "cd $randstring$proj_path;"'
		for i in $(find . -type f); do
			cur_dir=$(pwd)
			D=$(dirname $i)
			B=$(basename $i)
			(cd $D && echo $(pwd)"/$B") || exit 1
			cd $cur_dir;
		done
	'
) 

#exclude files that have been made intentionally by us
back_files=$(echo $back_files | tr " " "\n" | grep -Fv "$(echo $transfered_files | tr " " "\n")" - | tr "\n" " ") 

#escape filenames - tar doesn't like files with ( and ) 
#get rid of random string from the path
temp="" 
for i in $back_files; do
	i=$(escape $i)
	temp="$temp "${i#*$randstring/}
done
back_files=$temp

message "Transferring back $(echo $back_files | wc -w) files..." &&
#put everything into an archive and copy with scp
ssh $R_USER@$R_MACHINE "cd $randstring && tar -cjvf $ARCH_NAME $back_files" &&
scp $R_USER@$R_MACHINE:$randstring/$ARCH_NAME . &&
#extract fresh meat
cd / && tar -xvjf $proj_path/$ARCH_NAME && cd $proj_path && rm $ARCH_NAME 

message "Removing director $randstring from remote machine..." 
#remove unneeded mess, leave needed mess
ssh $R_USER@$R_MACHINE "rm -rf $randstring"
