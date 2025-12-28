"""CIPHERDETECT MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from cipherdetect.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-cipherdetect[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-cipherdetect[mcp]'")
        return 1
    app = FastMCP("cipherdetect")

    @app.tool()
    def cipherdetect_scan(target: str) -> str:
        """Detect & crack classical ciphers (caesar/vigenere/xor) by scoring. Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0
