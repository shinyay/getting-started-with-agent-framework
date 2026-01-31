import os
import sys
from pathlib import Path
import socket

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

    host = os.getenv("DEVUI_HOST", "0.0.0.0")
    # Default to 8081: in Dev Containers, 8080 is frequently reused by other demos/tools and can
    # get into a flaky port-forwarding state in the VS Code embedded browser.
    port = int(os.getenv("DEVUI_PORT", "8081"))

    # Preflight: fail with a clear message if the port is already occupied.
    # (Uvicorn will raise Errno 98, but this is friendlier.)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
    except OSError as ex:
        if getattr(ex, "errno", None) == 98:  # address already in use
            raise RuntimeError(
                f"DevUI cannot start because {host}:{port} is already in use.\n\n"
                "Fix options:\n"
                "- Stop the existing process that is listening on that port, OR\n"
                "- Choose another port, e.g. set DEVUI_PORT=8081\n"
            ) from ex
        raise
    finally:
        sock.close()

    serve(
        entities=[workflow],
        host=host,
        port=port,
        auto_open=not no_open,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
