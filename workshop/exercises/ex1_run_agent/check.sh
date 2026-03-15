#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$SCRIPT_DIR/starter.py"

echo "=== Exercise 1: Check ==="

echo "[1/3] Syntax check..."
python3 -m py_compile "$FILE"
echo "  ✓ Syntax OK"

echo "[2/3] Structure check..."
python3 -c "
import ast, sys
with open('$FILE') as f:
    tree = ast.parse(f.read())

# Check for required patterns
source = open('$FILE').read()
checks = {
    'AzureCliCredential': 'AzureCliCredential' in source and 'TODO' not in source.split('AzureCliCredential')[0][-50:],
    'AzureAIAgentClient': 'AzureAIAgentClient' in source,
    'as_agent': 'as_agent' in source,
    'agent.run or .run(': '.run(' in source,
    'result.text': '.text' in source,
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
