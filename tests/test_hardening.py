"""Hardening tests: error paths, edge cases, and input validation."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cipherdetect.cli import main, _validate_args  # noqa: E402
from cipherdetect.core import analyze  # noqa: E402
import argparse


class TestCliMissingFile(unittest.TestCase):
    def test_missing_file_exits_1(self):
        """A nonexistent file path must produce exit code 1, not a traceback."""
        rc = main(["crack", "definitely_not_a_real_file_xyz123.txt"])
        self.assertEqual(rc, 1)

    def test_missing_file_message_goes_to_stderr(self):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            main(["crack", "nope_xyz.txt"])
        self.assertIn("error", buf.getvalue().lower())


class TestCliArgValidation(unittest.TestCase):
    def test_top_zero_exits_1(self):
        rc = main(["crack", "--text", "Hello World", "--top", "0"])
        self.assertEqual(rc, 1)

    def test_top_negative_exits_1(self):
        rc = main(["crack", "--text", "Hello World", "--top", "-5"])
        self.assertEqual(rc, 1)

    def test_max_key_len_zero_exits_1(self):
        rc = main(["crack", "--text", "Hello World", "--max-key-len", "0"])
        self.assertEqual(rc, 1)

    def test_max_key_len_over_limit_exits_1(self):
        rc = main(["crack", "--text", "Hello World", "--max-key-len", "200"])
        self.assertEqual(rc, 1)

    def test_valid_args_passes_validation(self):
        ns = argparse.Namespace(top=5, max_key_len=12)
        self.assertIsNone(_validate_args(ns))


class TestCliEmptyInput(unittest.TestCase):
    def test_empty_text_exits_1(self):
        """An empty --text argument must not crash and must exit 1."""
        rc = main(["crack", "--text", ""])
        self.assertEqual(rc, 1)

    def test_empty_file_exits_1(self):
        """An empty file must not crash and must exit 1."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"")
            fname = f.name
        try:
            rc = main(["crack", fname])
            self.assertEqual(rc, 1)
        finally:
            os.unlink(fname)


class TestAnalyzeHardening(unittest.TestCase):
    def test_analyze_empty_bytes_returns_empty(self):
        """analyze(b"") must return an empty list, not crash."""
        result = analyze(b"")
        self.assertEqual(result, [])

    def test_analyze_wrong_type_raises(self):
        """analyze() must raise TypeError if given a non-bytes argument."""
        with self.assertRaises(TypeError):
            analyze("not bytes")

    def test_analyze_clamps_top(self):
        """Core clamping: very large top value should not crash."""
        result = analyze(b"Hello World", top=999)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class TestMcpServerImports(unittest.TestCase):
    def test_mcp_server_imports_without_error(self):
        """mcp_server module must import cleanly (no broken scan/to_json refs)."""
        import importlib
        # This should not raise ImportError
        mod = importlib.import_module("cipherdetect.mcp_server")
        self.assertTrue(callable(mod.serve))


if __name__ == "__main__":
    unittest.main()
