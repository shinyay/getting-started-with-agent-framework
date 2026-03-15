#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Exercise 7: Capstone Check ==="

# Find Python files (excluding __pycache__)
PY_FILES=$(find "$SCRIPT_DIR" -name "*.py" -not -path "*/__pycache__/*" 2>/dev/null)

if [ -z "$PY_FILES" ]; then
    echo "  ✗ No Python files found in $SCRIPT_DIR"
    echo "  Create your solution as .py file(s) in this directory"
    exit 1
fi
echo "[1/3] Found Python files:"
echo "$PY_FILES" | sed 's/^/    /'

echo "[2/3] Syntax check..."
echo "$PY_FILES" | while read -r f; do
    python3 -m py_compile "$f"
    echo "  ✓ $f"
done

echo "[3/3] Basic pattern check..."
AGENT_FOUND=false
for f in $PY_FILES; do
    if grep -qi 'agent\|workflow\|as_agent\|WorkflowBuilder' "$f"; then
        AGENT_FOUND=true
        break
    fi
done

if [ "$AGENT_FOUND" = false ]; then
    echo "  ⚠ Warning: No agent/workflow patterns found in your code"
    echo "  Make sure your solution uses Agent Framework APIs"
fi
echo "  ✓ Pattern check done"

echo ""
echo "=== Capstone checks passed! ==="
echo "Run your solution to test it against Azure."
