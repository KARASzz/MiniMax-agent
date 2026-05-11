"""Bridge the bundled official MiniMax MCP server into this project.

The official server is kept under ``MiniMax-MCP/``. This module only prepares
the shared project environment before importing it.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
MCP_DIR = PROJECT_DIR / "MiniMax-MCP"
DEFAULT_MCP_API_HOST = "https://api.minimax.chat"


def configure_mcp_environment(resource_mode: str | None = None) -> None:
    """Set defaults required by the official MCP server.

    ``MINIMAX_API_KEY`` remains the single shared key for the whole project.
    ``MINIMAX_API_HOST`` falls back to the official MCP mainland host used by
    the bundled MiniMax-MCP demo config.
    """
    from config import API_KEY, OUTPUT_DIR

    if not MCP_DIR.exists():
        raise RuntimeError(f"未找到官方 MCP 目录: {MCP_DIR}")

    os.environ.setdefault("MINIMAX_API_KEY", API_KEY)
    mcp_api_host = os.environ.get("MINIMAX_MCP_API_HOST")
    if mcp_api_host:
        os.environ["MINIMAX_API_HOST"] = mcp_api_host
    else:
        os.environ.setdefault("MINIMAX_API_HOST", DEFAULT_MCP_API_HOST)
    os.environ.setdefault("MINIMAX_MCP_BASE_PATH", OUTPUT_DIR)
    os.environ.setdefault("FASTMCP_LOG_LEVEL", "WARNING")
    if resource_mode:
        os.environ.setdefault("MINIMAX_API_RESOURCE_MODE", resource_mode)

    mcp_dir_str = str(MCP_DIR)
    if mcp_dir_str not in sys.path:
        sys.path.insert(0, mcp_dir_str)


def load_official_server(resource_mode: str | None = "local") -> Any:
    """Import and return the bundled official ``minimax_mcp.server`` module."""
    configure_mcp_environment(resource_mode=resource_mode)
    try:
        return importlib.import_module("minimax_mcp.server")
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        raise RuntimeError(
            f"官方 MCP 依赖缺失: {missing}。请先运行 pip install -r requirements.txt"
        ) from exc


def result_text(result: Any) -> str:
    """Extract readable text from an MCP TextContent-style result."""
    if hasattr(result, "text"):
        return str(result.text)
    if isinstance(result, list):
        return "\n".join(result_text(item) for item in result)
    return str(result)


def run_mcp_server() -> None:
    """Start the bundled official MCP server with project defaults."""
    server = load_official_server(resource_mode=os.environ.get("MINIMAX_API_RESOURCE_MODE", "local"))
    # Call the FastMCP runner directly so stdio transport stays clean for MCP clients.
    server.mcp.run()
