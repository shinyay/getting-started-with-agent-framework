#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STARTER="$SCRIPT_DIR/starter.py"
ENTITY_INIT="$SCRIPT_DIR/starter_entity/__init__.py"
ENTITY_WF="$SCRIPT_DIR/starter_entity/workflow.py"

echo "=== Exercise 6: Check ==="

# ---------------------------------------------------------------
echo "[1/5] Syntax check..."
python3 -m py_compile "$STARTER"
echo "  ✓ starter.py — Syntax OK"
python3 -m py_compile "$ENTITY_WF"
echo "  ✓ starter_entity/workflow.py — Syntax OK"

# ---------------------------------------------------------------
echo "[2/5] Entity structure..."
if [ ! -f "$ENTITY_INIT" ]; then
    echo "  ✗ starter_entity/__init__.py is missing"
    echo "  Hint: DevUI discovers entities via __init__.py — make sure the file exists"
    exit 1
fi
if ! grep -q 'workflow' "$ENTITY_INIT"; then
    echo "  ✗ starter_entity/__init__.py does not export 'workflow'"
    echo "  Hint: Add 'from .workflow import workflow' to __init__.py"
    exit 1
fi
echo "  ✓ Entity package exports workflow"

# ---------------------------------------------------------------
echo "[3/5] starter.py structure..."
python3 -c "
import sys

source = open('$STARTER').read()
checks = {
    'serve import': 'serve' in source,
    'entities keyword': 'entities' in source,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    print(f'  ✗ Missing patterns: {failed}')
    print('  Hint: Make sure you have filled in all TODO sections in starter.py')
    sys.exit(1)
print('  ✓ Required patterns found in starter.py')
"

# ---------------------------------------------------------------
echo "[4/5] workflow.py structure..."
python3 -c "
import sys

source = open('$ENTITY_WF').read()
checks = {
    'WorkflowBuilder': 'WorkflowBuilder' in source,
    'register_agent': 'register_agent' in source,
    'set_start_executor': 'set_start_executor' in source,
    'add_edge': 'add_edge' in source,
    '.build()': '.build()' in source,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    print(f'  ✗ Missing patterns: {failed}')
    print('  Hint: Make sure you have filled in all TODO sections in workflow.py')
    sys.exit(1)
print('  ✓ Required patterns found in workflow.py')
"

# ---------------------------------------------------------------
echo "[5/5] TODO check..."
has_todos=0
for f in "$STARTER" "$ENTITY_WF"; do
    if grep -q 'TODO' "$f"; then
        echo "  ⚠ $(basename "$f"): TODO markers still present"
        grep -n 'TODO' "$f" | sed 's/^/    /'
        has_todos=1
    fi
done
if [ "$has_todos" -eq 1 ]; then
    echo "  ✗ Resolve all TODOs before proceeding"
    exit 1
fi
echo "  ✓ No remaining TODOs"

echo ""
echo "=== All checks passed! ==="
echo "Next: Launch DevUI with: python3 -u $STARTER"
