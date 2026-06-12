"""Core cipher-detection engine.

Scores candidate plaintexts against English letter/bigram frequencies plus a
common-word bonus, then runs Caesar, Vigenere and single-byte XOR crackers and
ranks every candidate decryption by likelihood.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

# Relative English letter frequencies (percent). Source: standard corpus stats.
_ENGLISH_FREQ = {
    "a": 8.167, "b": 1.492, "c": 2.782, "d": 4.253, "e": 12.702,
    "f": 2.228, "g": 2.015, "h": 6.094, "i": 6.966, "j": 0.153,
    "k": 0.772, "l": 4.025, "m": 2.406, "n": 6.749, "o": 7.507,
    "p": 1.929, "q": 0.095, "r": 5.987, "s": 6.327, "t": 9.056,
    "u": 2.758, "v": 0.978, "w": 2.360, "x": 0.150, "y": 1.974,
    "z": 0.074,
}

_COMMON_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their",
    "what", "so", "if", "is", "are", "was", "were", "been", "has",
    "attack", "secret", "message", "hello", "world",
}

_WORD_RE = re.compile(r"[a-z]+")


@dataclass
class Candidate:
    """A single candidate decryption with its score and metadata."""

    cipher: str            # caesar | vigenere | xor
    key: str               # human-readable key (shift, keyword, or byte)
    plaintext: str         # decrypted text
    score: float           # higher = more English-like
    severity: str = ""     # info | low | medium | high (assigned by analyze)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _letter_freq_chi2(text: str) -> float:
    """Chi-squared distance from English letter frequencies (lower = better)."""
    letters = [c for c in text.lower() if c.isalpha() and c.isascii()]
    n = len(letters)
    if n == 0:
        return 1e9
    counts = {c: 0 for c in _ENGLISH_FREQ}
    for c in letters:
        if c in counts:
            counts[c] += 1
    chi2 = 0.0
    for c, expected_pct in _ENGLISH_FREQ.items():
        expected = expected_pct / 100.0 * n
        observed = counts[c]
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected
    return chi2 / n


def _printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    good = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
    return good / len(text)


def _word_bonus(text: str) -> float:
    words = _WORD_RE.findall(text.lower())
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in _COMMON_WORDS)
    return hits / len(words)


def score_english(text: str) -> float:
    """Return an English-likeness score. Higher is more English-like.

    Combines printable-character ratio, inverse letter-frequency chi-squared,
    and a common-word bonus into a single comparable score.
    """
    if not text:
        return 0.0
    printable = _printable_ratio(text)
    if printable < 0.85:
        # Heavily penalize binary garbage so XOR junk never wins.
        return printable * 0.5
    chi2 = _letter_freq_chi2(text)
    freq_score = 1.0 / (1.0 + chi2)  # in (0, 1], 1 = perfect English freq
    word_score = _word_bonus(text)
    # Weighted blend. Word hits are strong evidence; freq is the base signal.
    return printable * (0.55 * freq_score + 0.45 * word_score) + 0.001 * len(text) ** 0


def crack_caesar(text: str) -> list[Candidate]:
    """Try all 25 non-trivial Caesar shifts; return scored candidates."""
    out: list[Candidate] = []
    for shift in range(1, 26):
        decoded = []
        for ch in text:
            if "a" <= ch <= "z":
                decoded.append(chr((ord(ch) - 97 - shift) % 26 + 97))
            elif "A" <= ch <= "Z":
                decoded.append(chr((ord(ch) - 65 - shift) % 26 + 65))
            else:
                decoded.append(ch)
        pt = "".join(decoded)
        out.append(Candidate("caesar", f"shift={shift}", pt, score_english(pt)))
    return out


def _vigenere_decrypt(text: str, key: str) -> str:
    out = []
    ki = 0
    klen = len(key)
    for ch in text:
        if ch.isalpha() and ch.isascii():
            base = 65 if ch.isupper() else 97
            k = ord(key[ki % klen]) - 97
            out.append(chr((ord(ch) - base - k) % 26 + base))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def _best_caesar_shift_for_column(column: str) -> int:
    best_shift, best_chi = 0, 1e18
    for shift in range(26):
        decoded = "".join(
            chr((ord(c) - 97 - shift) % 26 + 97) for c in column
        )
        chi = _letter_freq_chi2(decoded)
        if chi < best_chi:
            best_chi, best_shift = chi, shift
    return best_shift


def _ic(text: str) -> float:
    """Index of coincidence for lowercase letters."""
    letters = [c for c in text.lower() if c.isalpha() and c.isascii()]
    n = len(letters)
    if n < 2:
        return 0.0
    counts: dict[str, int] = {}
    for c in letters:
        counts[c] = counts.get(c, 0) + 1
    return sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def crack_vigenere(text: str, max_key_len: int = 12) -> list[Candidate]:
    """Estimate key length via index-of-coincidence, derive key per column."""
    letters = [c for c in text.lower() if c.isalpha() and c.isascii()]
    if len(letters) < 6:
        return []
    stripped = "".join(letters)
    candidates: list[Candidate] = []
    # Rank key lengths by how close their average column IC is to English (~0.066).
    scored_lengths: list[tuple[float, int]] = []
    for klen in range(1, min(max_key_len, len(stripped)) + 1):
        cols = [stripped[i::klen] for i in range(klen)]
        avg_ic = sum(_ic(col) for col in cols) / klen
        scored_lengths.append((abs(avg_ic - 0.0667), klen))
    scored_lengths.sort()
    for _, klen in scored_lengths[:4]:
        cols = [stripped[i::klen] for i in range(klen)]
        key = "".join(
            chr(_best_caesar_shift_for_column(col) % 26 + 97) for col in cols
        )
        pt = _vigenere_decrypt(text, key)
        candidates.append(
            Candidate("vigenere", f"key={key}", pt, score_english(pt),
                      notes=f"est_key_len={klen}")
        )
    return candidates


def crack_xor(data: bytes) -> list[Candidate]:
    """Try all 256 single-byte XOR keys; return scored candidates."""
    out: list[Candidate] = []
    for k in range(256):
        decoded = bytes(b ^ k for b in data)
        try:
            pt = decoded.decode("utf-8")
        except UnicodeDecodeError:
            pt = decoded.decode("latin-1")
        out.append(Candidate("xor", f"byte=0x{k:02x}", pt, score_english(pt)))
    return out


def _assign_severity(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    if score >= 0.18:
        return "low"
    return "info"


def analyze(raw: bytes, top: int = 5, max_key_len: int = 12) -> list[Candidate]:
    """Run every cracker and return the top-N ranked candidate decryptions.

    `raw` is the ciphertext bytes. Text-based ciphers (Caesar/Vigenere) use a
    best-effort UTF-8/latin-1 decode; XOR operates on raw bytes.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    candidates: list[Candidate] = []
    candidates.extend(crack_caesar(text))
    candidates.extend(crack_vigenere(text, max_key_len=max_key_len))
    candidates.extend(crack_xor(raw))

    candidates.sort(key=lambda c: c.score, reverse=True)
    ranked = candidates[: max(1, top)]
    for c in ranked:
        c.severity = _assign_severity(c.score)
    return ranked
