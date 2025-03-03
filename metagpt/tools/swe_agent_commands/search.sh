# @yaml
# signature: search_dir_and_preview <search_term> [<dir>]
# docstring: searches for search_term in all files in dir and give their code preview with line number if you think need a first look. The output will vary depending on the length of the search results, but the file path, line number & corresponding code or number of occurrences will always be output. If dir is not provided, searches in the current directory
# arguments:
#   search_term:
#     type: string
#     description: the term to search for
#     required: true
#   dir:
#     type: string
#     description: the directory to search in (if not provided, searches in the current directory)
#     required: false
search_dir_and_preview() {
    if [ $# -eq 1 ]; then
        local search_term="$1"
        local dir="./"
    elif [ $# -eq 2 ]; then
        local search_term="$1"
        if [ -d "$2" ]; then
            local dir="$2"
        else
            echo "Directory $2 not found"
            return
        fi
    else
        echo "Usage: search_dir_and_preview <search_term> [<dir>]"
        return
    fi
    dir=$(realpath "$dir")
    local matches=$(find "$dir" -type f -path '*.py' -exec grep -nIH -- "$search_term" {} + | cut -d: -f1 | sort | uniq -c)
<<COMMENT
    metches exmaple: 3 xx/xx/test_file.py
COMMENT

    local matches_with_line=$(find "$dir" -type f -path '*.py' -exec grep -nIH -- "$search_term" {} + | sort | uniq -c)
<<COMMENT
    matches_with_line example: 1 xx/xx/test_file.py:20: def func_test()
COMMENT

    # if no matches, return
    if [ -z "$matches" ]; then
        echo "No matches found for \"$search_term\" in $dir"
        return
    fi
    # Calculate total number of matches
    local num_matches=$(echo "$matches" | awk '{sum+=$1} END {print sum}')

    # calculate total number of files matched
    local num_files=$(echo "$matches" | wc -l | awk '{$1=$1; print $0}')
    # if num_files is > 100, print an error
    if [ $num_files -gt 100 ]; then
        echo "More than $num_files files matched for \"$search_term\" in $dir. Please narrow your search."
        return
    fi

    match_with_cnt=$(echo "$matches" | awk '{$2=$2; gsub(/^\.+\/+/, "./", $2); print $2 " ("$1" matches)"}')
<<COMMENT
    match_with_cnt example: xx/xx/test_file.py (3 matches)
COMMENT
    match_res=""
    match_res+="Found $num_matches matches for \"$search_term\" in $dir:\n"
    match_res+="$match_with_cnt\n"
    match_res+="End of matches for \"$search_term\" in $dir"

    match_line_res=""
<<COMMENT
    match_line_res example: xx/xx/test_file.py
                            10: def test_func()
                            20: a = test_func()
COMMENT
    match_line_res+="Found $num_matches matches for \"$search_term\" in $dir:\n"
    # transform matches_with_line format into match_line_res
    transform_res=$(echo "$matches_with_line" | awk -F ':' '
    {
        code="";
        for (i=3; i<=NF; i++) {
            code = code $i ":";
        }
        if (code != "") {
          code=substr(code, 1, length(code)-1)
        }

        split($1, arr, " ");
        file=arr[2];
        line=$2;

        if (file != current_file) {
            if (current_file != "") {
                print "";
            }
            print file;
            current_file = file;
        }
        print line ":" code;
    }
    ')

    match_line_res+="$transform_res\n"
    match_line_res+="End of matches for \"$search_term\" in $dir"

    matched_files=$(find "$dir" -type f -path '*.py' -exec grep -nIH -- "$search_term" {} + | cut -d: -f1)
    matched_lineno=$(find "$dir" -type f -path '*.py' -exec grep -nIH -- "$search_term" {} + | cut -d: -f2)
    files_arr=($matched_files)
    lineno_arr=($matched_lineno)
    length=${#files_arr[@]}

    preview_res=""
    preview_res+="Found $num_matches matches for \"$search_term\" in $dir. Founded files and there code preview with line number are under below\n"
    for (( idx=0; idx<$length; idx++ )); do
        file_abs_path=${files_arr[$idx]}
        lineno=${lineno_arr[$idx]}
        # preview head 3 lines
        lineno_sub=$(($lineno-3))
        if (( $lineno_sub < 0 )); then
            head_start_lineno=0
        else
            head_start_lineno=$lineno_sub
        fi
        head_content=$(sed -n "$(($head_start_lineno)),$(($lineno-1))p" "$file_abs_path" | nl -w 1 -ba -s ":" -v $head_start_lineno)

        # preview tail 5+1 lines, including the `lineno` line
        tail_content=$(sed -n "$(($lineno)),$(($lineno+5))p" "$file_abs_path" | nl -w 1 -ba -s ":" -v $lineno)

        preview_res+="\nFounded #$idx code block in $file_abs_path\n"
        preview_res+="$head_content\n"
        preview_res+="$tail_content\n"
    done

    preview_res+="End of matches for \"$search_term\" in $dir"
    preview_res_len=${#preview_res}
    if [ $preview_res_len -gt 20000 ]; then
        echo -e "$match_res"
    elif [ $preview_res_len -gt 10000 ]; then
        echo -e "$match_line_res"
    else
        echo -e "$preview_res"
    fi
}


# @yaml
# signature: search_file <search_term> [<file>]
# docstring: searches for search_term in file. If file is not provided, searches in the current open file
# arguments:
#   search_term:
#     type: string
#     description: the term to search for
#     required: true
#   file:
#     type: string
#     description: the file to search in (if not provided, searches in the current open file)
#     required: false
search_file() {
    # Check if the first argument is provided
    if [ -z "$1" ]; then
        echo "Usage: search_file <search_term> [<file>]"
        return
    fi
    # Check if the second argument is provided
    if [ -n "$2" ]; then
        # Check if the provided argument is a valid file
        if [ -f "$2" ]; then
            local file="$2"  # Set file if valid
        else
            echo "Usage: search_file <search_term> [<file>]"
            echo "Error: File name $2 not found. Please provide a valid file name."
            return  # Exit if the file is not valid
        fi
    else
        # Check if a file is open
        if [ -z "$CURRENT_FILE" ]; then
            echo "No file open. Use the open command first."
            return  # Exit if no file is open
        fi
        local file="$CURRENT_FILE"  # Set file to the current open file
    fi
    local search_term="$1"
    file=$(realpath "$file")
    # Use grep to directly get the desired formatted output
    local matches=$(grep -nH -- "$search_term" "$file")
    # Check if no matches were found
    if [ -z "$matches" ]; then
        echo "No matches found for \"$search_term\" in $file"
        return
    fi
    # Calculate total number of matches
    local num_matches=$(echo "$matches" | wc -l | awk '{$1=$1; print $0}')

    # calculate total number of lines matched
    local num_lines=$(echo "$matches" | cut -d: -f1 | sort | uniq | wc -l | awk '{$1=$1; print $0}')
    # if num_lines is > 100, print an error
    if [ $num_lines -gt 100 ]; then
        echo "More than $num_lines lines matched for \"$search_term\" in $file. Please narrow your search."
        return
    fi

    # Print the total number of matches and the matches themselves
    echo "Found $num_matches matches for \"$search_term\" in $file:"
    echo "$matches" | cut -d: -f1-2 | sort -u -t: -k2,2n | while IFS=: read -r filename line_number; do
        echo "Line $line_number:$(sed -n "${line_number}p" "$file")"
    done
    echo "End of matches for \"$search_term\" in $file"
}

# @yaml
# signature: find_file <file_name> [<dir>]
# docstring: finds all files with the given name in dir. If dir is not provided, searches in the current directory
# arguments:
#   file_name:
#     type: string
#     description: the name of the file to search for
#     required: true
#   dir:
#     type: string
#     description: the directory to search in (if not provided, searches in the current directory)
#     required: false
find_file() {
    if [ $# -eq 1 ]; then
        local file_name="$1"
        local dir="./"
    elif [ $# -eq 2 ]; then
        local file_name="$1"
        if [ -d "$2" ]; then
            local dir="$2"
        else
            echo "Directory $2 not found"
            return
        fi
    else
        echo "Usage: find_file <file_name> [<dir>]"
        return
    fi

    dir=$(realpath "$dir")
    local matches=$(find "$dir" -type f -name "$file_name")
    # if no matches, return
    if [ -z "$matches" ]; then
        echo "No matches found for \"$file_name\" in $dir"
        return
    fi
    # Calculate total number of matches
    local num_matches=$(echo "$matches" | wc -l | awk '{$1=$1; print $0}')
    echo "Found $num_matches matches for \"$file_name\" in $dir:"
    echo "$matches" | awk '{print $0}'
}
