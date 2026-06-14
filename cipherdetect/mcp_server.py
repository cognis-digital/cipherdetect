"""CIPHERDETECT MCP server — exposes analyze() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
import json as _json
from cipherdetect.core import analyze


def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-cipherdetect[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("Install the MCP extra: pip install 'cognis-cipherdetect[mcp]'")
        return 1
    app = FastMCP("cipherdetect")

    @app.tool()
    def cipherdetect_scan(target: str) -> str:
        """Detect & crack classical ciphers (caesar/vigenere/xor) by scoring. Returns JSON findings."""
        if not target:
            return _json.dumps({"error": "empty input", "candidates": []})
        candidates = analyze(target.encode("utf-8", errors="replace"))
        return _json.dumps({"candidates": [c.to_dict() for c in candidates]}, indent=2)

    app.run()
    return 0
