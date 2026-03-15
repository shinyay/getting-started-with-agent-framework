#!/usr/bin/env bash
# ---------------------------------------------------------------
# Exercise 2 — Structure Check
#
# Verifies that starter.py compiles, contains the expected
# constructs, and has no remaining TODO markers.
#
# Usage:  bash workshop/exercises/ex2_web_search/check.sh
# ---------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE="${SCRIPT_DIR}/starter.py"

pass=0
fail=0

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✅  ${label}"
    pass=$((pass + 1))
  else
    echo "  ❌  ${label}"
    fail=$((fail + 1))
  fi
}

echo ""
echo "=== Exercise 2: Hosted Web Search Tool ==="
echo ""

# 1. Syntax check
check "Python syntax is valid" python3 -m py_compile "${FILE}"

# 2. Structure checks
check "HostedWebSearchTool is instantiated" \
  grep -qE 'HostedWebSearchTool\s*\(' "${FILE}"

check "additional_properties (or tool_properties) is configured" \
  grep -qE '(additional_properties|tool_properties)\s*=' "${FILE}"

check "tools= is passed to as_agent()" \
  grep -qE '^[^#]*tools\s*=\s*\[' "${FILE}"

check "agent.run() is called" \
  grep -qE '^[^#]*await\s+.*\.run\s*\(' "${FILE}"

# 3. No remaining TODOs
check "No remaining TODO markers" \
  bash -c "! grep -qE '# *TODO' '${FILE}'"

echo ""
echo "Results:  ${pass} passed,  ${fail} failed"
if [ "${fail}" -gt 0 ]; then
  echo ""
  echo "Keep going — review the README hints and fill in the remaining TODOs."
  exit 1
fi
echo ""
echo "All checks passed! Run your solution against Azure:"
echo "  python workshop/exercises/ex2_web_search/starter.py"
