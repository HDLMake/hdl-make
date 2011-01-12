#!/bin/bash
# The aim of the script is to allow
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
R_MACHINE="localhost"
R_USER="pawel"
ARCH_NAME="arch.tar"

#if [ $# -ne 1 ];then
#	usage $0
#fi
#if [ ! -d $1 ]; then
#	echo "$1 is not a directory"
#	usage $0
#fi  

#ommit leading '/'
#proj_path=$(abs_path $1)
#proj_path=${proj_path%.}
#proj_path=${proj_path%/}

qpf="$(ls|grep -e '.*\.qpf$')"

if [ $(echo $qpf | wc -w) -ne 1 ]; then
	echo 'No .qpf or too much files found' >&2
	echo 'Exiting' >&2
	exit 1
fi

qsf="$(ls|grep -e '.*\.qsf$')"
if [ $(echo $qsf | wc -w) -ne 1 ]; then
	echo 'No .qsf or too much files found' >&2
	echo 'Exiting' >&2
	exit 1
fi

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
		echo 'Taking the former into account' >72
		extra_files=$(cat extra-files)
	fi
fi

# extract vhdl files, pre- and post-flow scripts from the .qsf file
vhdl_files=$(awk '{if($0 ~ /VHDL_FILE/) {print $4}}' $qsf)
pre_flow=$(awk '{if ($0 ~ /PRE_FLOW_SCRIPT_FILE/) {print gensub(/".*:([^"]+)"/, "\\1", "g", $4)}}' $qsf)
post_flow=$(awk '{if($0 ~ /POST_FLOW_SCRIPT_FILE/) {print gensub(/".*:([^"]+)"/, "\\1", "g", $4)}}' $qsf)

# extract design name from the name of .qsf file (leave the longest part before dot)
design_name=${qsf%.*}

# create a random string for a new remote catalogue
temp=$(date | md5sum | md5sum )
randstring="${temp:2:10}"
#randstring="3c4fee127b"

# convert vhdl files names to their absulte paths
vhdl_files=$(abs_path_list $vhdl_files)

# convert extra-files' names to their absolute path
extra_files=$(abs_path_list $extra_files)

# convert other file names to their absulute names
qsf=$(abs_path $qsf)
qpf=$(abs_path $qpf)
pre_flow=$(abs_path $pre_flow)
post_flow=$(abs_path $post_flow)

message "Creating synthesis director named $randstring on the remote machine..." &&
ssh $R_USER@$R_MACHINE "mkdir -p $randstring" &&
message "Transferring vhdl files, project files and scripts to remote machine..." &&
tar -cvjf - $extra_files $vhdl_files $pre_flow $post_flow $qpf $qsf | ssh $R_USER@$R_MACHINE "(cd $randstring; tar xjf -)" &&
ssh $R_USER@$R_MACHINE "cd $randstring/home/pawel/wrdev/hdl; mkdir bin; echo touch > dupa" &&
message "Running synthesis with quartus..." &&
ssh $R_USER@$R_MACHINE "cd "$randstring""$(pwd)"; export TERM=linux; pwd;/home/pawel/altera/10.0sp1/quartus/bin/quartus_sh --flow compile $design_name" &&
message "Creating list of files that should be copied back..." &&
back_files=$(ssh "$R_USER"'@'"$R_MACHINE" "cd $randstring;"'
	for i in $(find . -type f); do
		cur_dir=$(pwd)
        D=$(dirname $i)
        B=$(basename $i)
        (cd $D && echo $(pwd)"/$B") || exit 1
        cd $cur_dir;
	done'
) &&
back_files=$(echo $back_files | tr " " "\n" | grep -Fv "$(echo $qsf $qpf $pre_flow $post_flow $extra_files $vhdl_files | tr " " "\n")" - | tr "\n" " ")

#get rid of random string prefix from the path to the files
temp=""
for i in $back_files; do
	i=$(escape $i)
	temp="$temp "${i#*$randstring/}
done
back_files=$temp

message "Transferring back $(echo $back_files | wc -w) files..." &&
ssh $R_USER@$R_MACHINE "cd $randstring && tar -cjvf $ARCH_NAME $back_files" && 
scp $R_USER@$R_MACHINE:$randstring/$ARCH_NAME . &&
proj_path=$(pwd) && cd / && tar -xjf $proj_path/$ARCH_NAME && cd $proj_path && rm $ARCH_NAME 
message "Removing director $randstring from remote machine..." 
ssh $R_USER@$R_MACHINE "rm -rf $randstring"
