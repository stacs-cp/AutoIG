BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pushd $BIN_DIR

for s in conjure savilerow mininzinc irace ortools yuck runsolver
do
    bash install-${s}.sh
done

popd
