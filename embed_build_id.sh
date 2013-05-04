#!/bin/bash

commit_line=$(git log | head -1)
commit_string=$(echo $commit_line | awk '{print $2}')

date_line=$(git log | head -3 | tail -1)
date_string=$(echo $date_line | awk '{print $6 $3 $4}')

embed_string='"'$(echo "$date_string:${commit_string:0:6}")'"'

build_hash_path="src/build_hash.py"
echo 'BUILD_ID = '"$embed_string" > $build_hash_path
