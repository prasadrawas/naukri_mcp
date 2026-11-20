"""
CLI entry point for running naukri-mcp server:
python -m naukri_mcp [--transport stdio|sse] [--port 8000]
"""
import os
import sys
import argparse
from pathlib import Path

# Add project and parent roots to sys.path so standalone and subfolder execution both work
for root_path in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent]:
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

from naukri_mcp.server import run_server


def main():
    parser = argparse.ArgumentParser(description="naukri-mcp: Model Context Protocol Server for Naukri.com")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio", help="Transport mode (default: stdio)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port for SSE mode (default: PORT env or 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE mode (default: 0.0.0.0)")
    args = parser.parse_args()

    run_server(transport=args.transport, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
