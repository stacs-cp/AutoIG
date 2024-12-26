#!/bin/bash

: <<'COMMENT'
 Tests for calls to conjure_solve()

 Runs all scripts in the conjure_solve-tests directory, to ensure that Conjure is able to find binaries for solvers: chuffed, kissat, and or-tools 

 Ensure that conjure is able to recognize the paths to solver binaries inside container environment. 
COMMENT

# Lines being checked for
lines=(
    "Copying solution to:"
)

testsPassed=0
testsRun=0

start=$(date +%s)

# Loop through each script in the tests directory
for file in conjure_solve-tests/*; do
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
    printf "\e[32mAll tests passed for Conjure: %d/%d! :D\e[0m\n" "$testsPassed" "$testsRun"
    exit 0
else
    printf "\e[31mSome cases failing for Conjure, only %d/%d passed.\e[0m\n" "$testsPassed" "$testsRun"
    exit 1
fi
