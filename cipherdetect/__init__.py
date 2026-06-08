"""CIPHERDETECT - detect and crack classical ciphers by scoring.

A defensive/forensics analysis tool that inspects ciphertext you own and
automatically identifies and decrypts classical ciphers (Caesar, Vigenere,
single-byte XOR) using English-likeness scoring.

Standard library only. Zero install.
"""
from .core import (
    Candidate,
    analyze,
    score_english,
    crack_caesar,
    crack_vigenere,
    crack_xor,
)

TOOL_NAME = "cipherdetect"
TOOL_VERSION = "1.0.0"

__all__ = [
    "TOOL_NAME",
    "TOOL_VERSION",
    "Candidate",
    "analyze",
    "score_english",
    "crack_caesar",
    "crack_vigenere",
    "crack_xor",
]
