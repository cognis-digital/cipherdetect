"""Smoke tests for CIPHERDETECT. Standard library only, no network."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cipherdetect import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    analyze,
    score_english,
    crack_caesar,
    crack_vigenere,
    crack_xor,
)
from cipherdetect.cli import main  # noqa: E402


def _caesar_encrypt(text: str, shift: int) -> str:
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


class TestScoring(unittest.TestCase):
    def test_english_beats_garbage(self):
        eng = score_english("the attack begins at dawn the secret word is falcon")
        junk = score_english("zxqwk vbnmh jklop qrtyu wzxcv bnmlk jhgfd")
        self.assertGreater(eng, junk)

    def test_empty(self):
        self.assertEqual(score_english(""), 0.0)


class TestCaesar(unittest.TestCase):
    def test_crack_caesar_recovers_plaintext(self):
        plain = "The attack begins at dawn. The secret word is falcon."
        cipher = _caesar_encrypt(plain, 3)
        cands = crack_caesar(cipher)
        best = max(cands, key=lambda c: c.score)
        self.assertEqual(best.plaintext, plain)
        self.assertEqual(best.key, "shift=3")


class TestVigenere(unittest.TestCase):
    def test_crack_vigenere_finds_keyword(self):
        # Encrypt a long English passage with key "lemon".
        plain = (
            "the quick brown fox jumps over the lazy dog while the "
            "secret message remains hidden inside the ancient cipher text "
            "that we must carefully analyze to recover the plaintext now"
        )
        key = "lemon"
        enc = []
        ki = 0
        for ch in plain:
            if ch.isalpha():
                k = ord(key[ki % len(key)]) - 97
                enc.append(chr((ord(ch) - 97 + k) % 26 + 97))
                ki += 1
            else:
                enc.append(ch)
        cipher = "".join(enc)
        cands = crack_vigenere(cipher, max_key_len=8)
        self.assertTrue(cands)
        best = max(cands, key=lambda c: c.score)
        self.assertEqual(best.key, "key=lemon")
        self.assertIn("secret message", best.plaintext)


class TestXor(unittest.TestCase):
    def test_crack_xor_single_byte(self):
        plain = b"The attack begins at dawn the secret word is falcon now"
        k = 0x42
        data = bytes(b ^ k for b in plain)
        cands = crack_xor(data)
        best = max(cands, key=lambda c: c.score)
        self.assertEqual(best.plaintext, plain.decode())
        self.assertEqual(best.key, "byte=0x42")


class TestAnalyze(unittest.TestCase):
    def test_analyze_ranks_caesar_top(self):
        plain = "The attack begins at dawn. The secret word is falcon."
        cipher = _caesar_encrypt(plain, 5)
        cands = analyze(cipher.encode(), top=5)
        self.assertTrue(cands)
        self.assertEqual(cands[0].plaintext, plain)
        self.assertEqual(cands[0].severity, "high")


class TestCli(unittest.TestCase):
    def test_version_constants(self):
        self.assertEqual(TOOL_NAME, "cipherdetect")
        self.assertTrue(TOOL_VERSION)

    def test_cli_text_json_finding_exit2(self):
        # Caesar shift=3 of a clear English sentence -> a confident finding.
        cipher = _caesar_encrypt("the attack begins at dawn the secret word", 3)
        rc = main(["crack", "--text", cipher, "--format", "json"])
        self.assertEqual(rc, 2)

    def test_cli_no_command_returns_1(self):
        rc = main([])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
