#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$SCRIPT_DIR/starter.py"

echo "=== Exercise 5: Check ==="

echo "[1/3] Syntax check..."
python3 -m py_compile "$FILE"
echo "  ✓ Syntax OK"

echo "[2/3] Structure check..."
python3 -c "
import sys

source = open('$FILE').read()

checks = {
    'WorkflowBuilder usage': 'WorkflowBuilder' in source and source.count('WorkflowBuilder') >= 2,
    'set_start_executor call': 'set_start_executor' in source and 'set_start_executor(' in source,
    'at least 4 add_edge calls': source.count('.add_edge(') >= 4,
    'run_stream call': 'run_stream' in source and 'run_stream(' in source,
    'event handling (AgentRunUpdateEvent or ExecutorCompletedEvent)': (
        ('AgentRunUpdateEvent' in source and 'isinstance' in source)
        or ('ExecutorCompletedEvent' in source and 'isinstance' in source)
    ),
    'at least 3 different agent names': (
        sum(1 for name in ['coordinator', 'venue', 'catering', 'budget_analyst', 'booking']
            if 'name=\"' + name + '\"' in source or \"name='\" + name + \"'\" in source) >= 3
    ),
}

failed = [k for k, v in checks.items() if not v]
if failed:
    print(f'  ✗ Missing patterns:')
    for f in failed:
        print(f'    - {f}')
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
