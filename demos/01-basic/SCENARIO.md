# Demo 01 - Basic: cracking an unknown classical cipher

You are doing forensics on an artifact you own (e.g. a string pulled from a
config file, a CTF challenge, or a legacy app's "obfuscated" data). You do not
know which classical cipher was used. CIPHERDETECT tries Caesar, Vigenere and
single-byte XOR, scores every candidate decryption for English-likeness, and
ranks them so the real plaintext rises to the top.

## Input

`ciphertext.txt` contains a Caesar-shifted message (shift = 3):

```
Wkh dwwdfn ehjlqv dw gdzq. Wkh vhfuhw zrug lv idofrq.
```

## Run it

Table output (human triage):

```bash
python -m cipherdetect crack demos/01-basic/ciphertext.txt
```

JSON output (pipelines / automation):

```bash
python -m cipherdetect crack demos/01-basic/ciphertext.txt --format json
```

Self-contained HTML report (shareable UI):

```bash
python -m cipherdetect crack demos/01-basic/ciphertext.txt \
    --format html -o report.html
```

## Expected result

The top-ranked candidate is the Caesar `shift=3` decryption:

```
The attack begins at dawn. The secret word is falcon.
```

It is tagged severity `high`. Because a confident decryption was found, the
process exits with code **2** (a "finding"), which automation can detect.

## Try inline text

```bash
python -m cipherdetect crack --text "Khoor Zruog"
```
