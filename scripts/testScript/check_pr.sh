#!/bin/bash

# Runs all scripts put in ./tests and makes sure that the run at some point contains a provided line:

# Lines being checked for
lines=(
    "# Best configurations (first number is the configuration ID; listed from best to worst according to the sum of ranks):"
    "# Best configurations as commandlines (first number is the configuration ID; same order as above):"
)

testsPassed=0
testsRun=0

start=$(date +%s)

# Loop through each script in the tests directory
for file in pr_tests/*; do
    ((testsRun++))
    # Check if file
    if [[ -f "$file" ]]; then

        # Run contents of file
        output=$(bash "$file")
        all_lines_found=true

        # Check for each line in the array
        for line in "${lines[@]}"; do
            if [[ "$output" != *"$line"* ]]; then
                all_lines_found=false
                echo "Test $testsRun: $file failed, line not found: $line"
            fi
        done

        # If all lines are found, count as passed
        if $all_lines_found; then
            echo "Test $testsRun: $file passed, all lines found in output"
            ((testsPassed++))
        fi
    fi
done

# Final results
if [[ "$testsRun" -eq "$testsPassed" ]]; then
    printf "\e[32mAll tests passed: %d/%d! :D\e[0m\n" "$testsPassed" "$testsRun"
    exit 0
else
    printf "\e[31mSome cases failing, only %d/%d passed.\e[0m\n" "$testsPassed" "$testsRun"
    exit 1
fi

# Record end time and calculate elapsed time
end=$(date +%s)
elapsedTime=$((end - start))

# Display time elapsed
echo "Time elapsed: $elapsedTime seconds"
