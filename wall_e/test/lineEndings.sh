#!/bin/bash

traverse_files(){
	echo "layer="$1
	local files_in_current_folder
	mapfile -t files_in_current_folder < <( ls | tr '\n' '\n' )
	local index
	for (( index=0; index < ${#files_in_current_folder[@]}; index++ ))
	do
		echo ${files_in_current_folder[$index]}
		if [ -d "${files_in_current_folder[$index]}" ]
		then
			echo -e "\tits a directory"
			local current_directory=$(pwd)
			echo "going to ${files_in_current_folder[$index]} from $current_directory"
			cd "${files_in_current_folder[$index]}"
			traverse_files $(expr $1 + 1)
			if [ $? -eq 1 ]; then
				return 1
			fi
			echo "going back to $current_directory"
			cd "$current_directory"
			# echo "back at ${files_in_current_folder[$index]}"

		else
            echo -e "\tits a regular file"
			fileType=$(file -i ${files_in_current_folder[$index]} | cut -d' ' -f2)
			if [ "$fileType" == "text/x-python;" ] || [ "$fileType" == "text/plain;" ]; then
				result=$(dos2unix < ${files_in_current_folder[$index]} | cmp - ${files_in_current_folder[$index]})
				if [ "$result" != "" ]; then
					echo ${files_in_current_folder[$index]} is not using linux line endings!
					return 1
				fi
			fi
			echo -e "\tits a regular file"
		fi

	done
}
traverse_files 1
