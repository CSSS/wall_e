#!/bin/bash

traverse_files(){
	echo "layer="$1
	local outter_files
	mapfile -t outter_files < <( ls | tr '\n' '\n' )
	local index
	for (( index=0; index < ${#outter_files[@]}; index++ ))
	do
		echo ${outter_files[$index]}
		if [ -d "${outter_files[$index]}" ]
		then
			echo -e "\tits a directory"
			dir=$(pwd)
			echo "going to ${outter_files[$index]} from $dir"
			cd "${outter_files[$index]}"
			traverse_files $(expr $1 + 1)
			if [ $? -eq 1 ]; then
				return 1
			fi
			echo "going back to $dir"
			cd "$dir"
			echo "back at ${outter_files[$index]}"

		else
			fileType=$(file -i ${outter_files[$index]} | cut -d' ' -f2)
			if [ "$fileType" == "text/x-python;" ] || [ "$fileType" == "text/plain;" ]; then
				result=$(dos2unix < ${outter_files[$index]} | cmp - ${outter_files[$index]})
				if [ "$result" != "" ]; then
					echo ${outter_files[$index]} is not using linux line endings!
					return 1
				fi
			fi
			echo -e "\tits a regular file"
		fi

	done
}
traverse_files 1
