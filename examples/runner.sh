#!/usr/bin/env bash

# usage: bash examples/runner.sh

set -Eeuo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$SCRIPT_DIR"/..
COMMANDS_FILE="$SCRIPT_DIR/suite.sh"

# used by `suite.sh`
UV="uv run --directory=${ROOT_DIR} main.py"

RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
DIM='\033[2m'
RESET='\033[0m'

# Parse the file: each command line is stored with its preceding comment as label.
labels=()
cmds=()
prev_line=""
while IFS= read -r line || [[ -n $line ]]; do
    # skip blank lines
    if [ -n "$line" ]; then
        # if the previous line is a comment, it becomes the label
        if [[ "$prev_line" == \#* ]]; then
            label=${prev_line# }
            continue
        fi

        # skip comments
        if [[ ! "$line" == \#* ]]; then
            labels+=("${label:-$line}")
            cmds+=("$line")
            prev_line="$line"
        fi
    fi
done < "$COMMANDS_FILE"

# Runs one command, printing it first. Returns the command's exit status.
run_command() {
    local label=$1
    local cmd=$2
    local index=$3
    local total=$4

    printf "\n${BLUE}[%d/%d] %s${RESET}\n" "$index" "$total" "$label"
    printf "${DIM}\$ %s${RESET}\n" "$cmd"

    # eval expands $UV and $ROOT_DIR inside each line
    eval "$cmd"
}

main() {
    local total=${#cmds[@]}
    local i status

    for (( i = 0; i < total; i++ )); do
        status=0
        run_command "${labels[$i]}" "${cmds[$i]}" "$((i + 1))" "$total" || status=$?

        if (( status != 0 )); then
            {
                printf "\n${RED}============================================================${RESET}\n"
                printf "${RED}✘ failed at step %d/%d (exit code %d): %s${RESET}\n" \
                    "$((i + 1))" "$total" "$status" "${labels[$i]}"
                printf "${RED}  command: %s${RESET}\n" "${cmds[$i]}"
                printf "${RED}============================================================${RESET}\n"
            } >&2
            exit "$status"
        fi
    done

    printf "\n${GREEN}✔ all %d commands completed successfully.${RESET}\n" "$total"
}

main "$@"