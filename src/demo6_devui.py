import os
import sys
from pathlib import Path

from agent_framework.devui import serve

def main() -> None:
    # Ensure the repository root is on sys.path so `entities/` can be imported
    # when running this file directly (sys.path[0] becomes `src/`).
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Import the workflow entity (this module loads .env fill-only and validates config at runtime).
    from entities.event_planning_workflow.workflow import workflow

    # Scott's demo uses auto_open=True; keep that default, but allow disabling in headless environments.
    no_open = (os.getenv("DEMO_NO_OPEN", "").strip().lower() in {"1", "true", "yes"})

    serve(
        entities=[workflow],
        host=os.getenv("DEVUI_HOST", "0.0.0.0"),
        port=int(os.getenv("DEVUI_PORT", "8080")),
        auto_open=not no_open,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
