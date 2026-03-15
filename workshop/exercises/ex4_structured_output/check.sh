#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$SCRIPT_DIR/starter.py"

echo "=== Exercise 4: Check ==="

echo "[1/3] Syntax check..."
python3 -m py_compile "$FILE"
echo "  ✓ Syntax OK"

echo "[2/3] Structure check..."
python3 -c "
import ast, sys

with open('$FILE') as f:
    source = f.read()
tree = ast.parse(source)

# Strip comment-only lines for pattern matching
code_lines = [line for line in source.splitlines() if not line.strip().startswith('#')]
code_only = '\n'.join(code_lines)

# Count classes inheriting from BaseModel
basemodel_classes = []
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        for base in node.bases:
            base_name = ''
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name == 'BaseModel':
                basemodel_classes.append(node.name)

if len(basemodel_classes) < 2:
    print(f'  ✗ Expected at least 2 classes inheriting BaseModel, found {len(basemodel_classes)}: {basemodel_classes}')
    print('  Hint: Define VenueInfoModel and VenueOptionsModel (TODO 1 & 2)')
    sys.exit(1)
print(f'  ✓ Found {len(basemodel_classes)} BaseModel classes: {basemodel_classes}')

checks = {
    'response_format keyword': 'response_format=' in code_only,
    '.value access': '.value' in code_only,
    'HostedWebSearchTool usage': 'HostedWebSearchTool(' in code_only and 'additional_properties' in code_only,
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
