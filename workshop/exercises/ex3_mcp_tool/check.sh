#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$SCRIPT_DIR/starter.py"

echo "=== Exercise 3: Check ==="

echo "[1/3] Syntax check..."
python3 -m py_compile "$FILE"
echo "  ✓ Syntax OK"

echo "[2/3] Structure check..."
python3 -c "
import sys

source = open('$FILE').read()
checks = {
    'MCPStdioTool import': 'MCPStdioTool' in source,
    'command= parameter': 'command=' in source,
    'args= parameter': 'args=' in source,
    '_require_command call': '_require_command(' in source and 'def _require_command' in source,
    'as_agent with tools=': 'as_agent' in source and 'tools=' in source,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    print(f'  ✗ Missing patterns: {failed}')
    print('  Hint: Make sure you have filled in all TODO sections')
    sys.exit(1)
print('  ✓ Required patterns found')
"

echo "[3/3] TODO check..."
if grep -q 'TODO' "$FILE"; then
    echo "  ⚠ Warning: TODO markers still present (have you completed all tasks?)"
    grep -n 'TODO' "$FILE" | sed 's/^/    /'
    exit 1
fi
echo "  ✓ No remaining TODOs"

echo ""
echo "=== All checks passed! ==="
echo "Next: Run against Azure with: python3 -u $FILE"
