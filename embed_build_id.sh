#!/bin/bash

commit_line=$(git log | head -1)
commit_string=$(echo $commit_line | awk '{print $2}')

date_line=$(git log | head -3 | tail -1)
date_string=$(echo $date_line | awk '{print $6 $3 $4}')

embed_string=$(echo "$date_string:${commit_string:0:6}")

if [ ! -f src/global_mod.py ]; then
    echo "Can't find src/global_mod.py file to put the versionID inside"
    exit 1
fi

global_mod_path="src/global_mod.py"
sed 's/^BUILD_ID =.*$/BUILD_ID = \"'$embed_string'"/' $global_mod_path > ${global_mod_path}_TMP
rm $global_mod_path 
mv ${global_mod_path}_TMP $global_mod_path

if [ ! -f src/global_mod.py ]; then
    echo "Shit! Something went wrong. Better check what happened to $global_mod_path"
    exit 1
fi