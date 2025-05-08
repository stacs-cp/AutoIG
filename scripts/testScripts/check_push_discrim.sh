#!/bin/bash

: <<'COMMENT'
 Tests for Discriminating Instance Generation

 Runs all scripts put in ./push_discrim_tests and makes sure that the run contains provided lines.

 Each script involves a full run of the macc problem, and each one uses a different solver. 

 Solvers tested with include chuffed, cpsat, gecode, picat, and yuck. 

 This script runs less intensive tests (macc runs with the small generator), and is intended for pushes to any branch.
COMMENT

# Lines being checked for
lines=(
    "too difficult instances for the favoured solver"
)

testsPassed=0
testsRun=0

start=$(date +%s)

# Loop through each script in the tests directory
for file in push_discrim_tests/*; do
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
    # Record end time and calculate elapsed time
    end=$(date +%s)
    elapsedTime=$((end - start))

    # Display time elapsed
    echo "Time elapsed: $elapsedTime seconds"
done

# Final results
if [[ "$testsRun" -eq "$testsPassed" ]]; then
    printf "\e[32mAll tests passed: %d/%d! :D\e[0m\n" "$testsPassed" "$testsRun"
    exit 0
else
    printf "\e[31mSome cases failing, only %d/%d passed.\e[0m\n" "$testsPassed" "$testsRun"
    exit 1
fi
