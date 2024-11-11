name="savilerow"

echo ""
echo "============= INSTALLING $name ==================="

# Checking if savile row exists at this path or not
if [ ! -d "/root/.local/bin/savilerow" ]; then
    echo "ERROR: saville row not found : (."
    exit 1
fi

echo "installation of minizinc was found :D"
