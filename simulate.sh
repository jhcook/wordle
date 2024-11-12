#!/usr/bin/env sh
#
# Iterate through the dictionary and find the most optimal
# word for solving all Wordle words. Outputs a CSV file with
# the results.
#
# Usage: ./simulate.sh <dictionary> <output_file>

set -o nounset
set -o errexit

# Check if the dictionary and output file are provided
if [ $# -lt 2 ]; then
  echo "Usage: ./simulate.sh <dictionary> <output_file>"
  exit 1
fi

# Check if the dictionary is a file. Otherwise, assume a string of words and
# create a temporary file to store the words.
if [ -f $1 ]; then
  DICTIONARY=$1
else
  trap "rm -f /tmp/words.$$" EXIT
  for word in $1; do
    # Remove newlines and extra spaces
    trimmed_word=$(echo $word | tr -d '\n' | xargs)
    echo $trimmed_word >> /tmp/words.$$
  done
  DICTIONARY=/tmp/words.$$
fi

OUTPUTFILE=$2

# Run a process and write info to file
run_process() { 
  local firstword=$1
  local good=0
  local bad=0
  for wrd in $(cat $DICTIONARY) ; do
    ./wordle.py -w $DICTIONARY --first $firstword --word $wrd -s >/dev/null && ((good++)) || ((bad++))
  done
  echo "$firstword,$good,$bad" >> $OUTPUTFILE
}

# Find out how many processors are available and always leave one free if possible.
# This is to prevent the system from becoming unresponsive.
NPROC=$(nproc)
if [ $NPROC -gt 1 ]; then
  ((NPROC--))
fi

# wait -n is not available in all versions of bash
# so we use an array to keep track of the process IDs
pids=()

# Write the header to the output file
echo "firstword,good,bad" > $OUTPUTFILE

# Iterate through the dictionary and run a simulation for each word as the first word
for word in $(cat $DICTIONARY) ; do
  run_process $word &
  # Get the process ID and add it to the array
  pids+=($!)
  # Check if the number of background processes has reached the maximum
  while [ ${#pids[@]} -ge $NPROC ]; do
    # Wait for any process to complete
    for pid in "${pids[@]}"; do
      if ! kill -0 $pid 2>/dev/null; then 
        # Remove the completed process ID from the array
        pids=(${pids[@]/$pid/})
        break
      fi
    done
    # Sleep briefly to avoid busy waiting
    sleep 1
  done
done

wait
