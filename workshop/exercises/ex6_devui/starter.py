# Exercise 6: Launch DevUI for Your Workflow
# Solution reference: src/demo6_devui.py

import os
import sys
from pathlib import Path
import socket

# TODO(1): Import 'serve' from agent_framework.devui
#   from agent_framework.devui import serve


def main() -> None:
    # Ensure the repository root is on sys.path so entity packages can be
    # imported when running this file directly (sys.path[0] becomes the
    # exercise directory).
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # ----------------------------------------------------------------
    # TODO(2): Import the workflow from your starter_entity package
    #   Hint: from workshop.exercises.ex6_devui.starter_entity.workflow import workflow
    # ----------------------------------------------------------------
    ...

    # Default to auto_open=True for convenience, but allow disabling in
    # headless environments (Codespaces, SSH, CI).
    no_open = os.getenv("DEMO_NO_OPEN", "").strip().lower() in {"1", "true", "yes"}

    # ----------------------------------------------------------------
    # TODO(3): Configure host and port (use env vars DEVUI_HOST and DEVUI_PORT with defaults)
    #   Hint: host = os.getenv("DEVUI_HOST", "0.0.0.0")
    #         port = int(os.getenv("DEVUI_PORT", "8080"))
    # ----------------------------------------------------------------
    ...

    # Preflight: fail with a clear message if the port is already occupied.
    # (Uvicorn would raise Errno 98, but this is friendlier.)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))  # noqa: F821 — host/port come from TODO(3)
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

    # ----------------------------------------------------------------
    # TODO(4): Call serve() with entities=[workflow], host, port, auto_open
    #   Hint:
    #     serve(
    #         entities=[workflow],
    #         host=host,
    #         port=port,
    #         auto_open=not no_open,
    #     )
    # ----------------------------------------------------------------
    ...


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
