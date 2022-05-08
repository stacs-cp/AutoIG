# get bin directory of this repo
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pushd $scriptDir; 
cd ../bin
binDir="$PWD"
popd

# conjure
export PATH=$binDir/conjure/2021-08-12-ef/:$PATH

# savile row
export PATH=$binDir/savilerow/2021-09-10/:$PATH

# fzn-chuffed
export PATH=$binDir/chuffed/0.10.4/:$PATH

# minion
export PATH=$binDir/minion/1.9.1/:$PATH

# cadical
export PATH=$binDir/cadical/1.3.0/:$PATH

# lingeling
export PATH=$binDir/lingeling/bcj-78ebb86/:$PATH

# irace
export PATH=$binDir/irace/bin:$PATH
export R_LIBS=$binDir/:$R_LIBS

# minizinc
export PATH=$PATH:$binDir/minizinc/MiniZincIDE-2.5.5-bundle-linux-x86_64/bin/
export LD_LIBRARY_PATH=$binDir/minizinc/MiniZincIDE-2.5.5-bundle-linux-x86_64/bin/lib:$LD_LIBRARY_PATH
