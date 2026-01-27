"""DevUI entity package.

DevUI directory discovery requires that each entity package exports either:
- `agent` (for agents)
- `workflow` (for workflows)

See: https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery?pivots=programming-language-python
"""

from .workflow import workflow
