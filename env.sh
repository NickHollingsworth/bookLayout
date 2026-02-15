# since this source's you need to 'dot run' it!
echo "python virtual environment:"
echo "source .venv/bin/activate"
echo ""

source .venv/bin/activate

alias py
which ${BASH_ALIASES[py]}
py -V

alias tr3="tree -L 3 | sed 's/├\|─\|│\|└/ /g'"

echo ""
echo "To exit python virtual environment: $ deactivate"
