"""
Fix Korean spacing inside make_pptx.py:

  English word/acronym + space + Korean particle  →  attach the particle.

Examples
  "perf layer 가"  →  "perf layer가"
  "KV 를"          →  "KV를"
  "memory 의"       →  "memory의"

Particles intentionally limited to one syllable (or short combinations) so
that "vLLM 위에" / "tensor 6 캐시" etc. — which are *word + word* and need
the space — are NOT touched. Only when the next character is a whitespace,
punctuation, or end-of-string after the particle do we attach.
"""
import re

PATH = "/home/pdaejun/bidaw/build/make_pptx.py"

# Single-syllable Korean particles
PARTICLES = (
    r"가|이|을|를|은|는|의|에|도|만|와|과|로|뿐"
    r"|에서|에게|으로|까지|부터|처럼|보다|마저"
)

PATTERN = re.compile(
    rf"([A-Za-z][A-Za-z0-9_\-]*) ({PARTICLES})(?=[\s,.\)\]·—:!?\"'`]|$)",
    re.MULTILINE,
)

with open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

new = PATTERN.sub(r"\1\2", src)

# Diff summary
import difflib
changes = []
for old, mod in zip(src.splitlines(), new.splitlines()):
    if old != mod:
        changes.append((old, mod))

print(f"Lines changed: {len(changes)}")
for old, mod in changes[:10]:
    print(f"  - {old.strip()[:80]}")
    print(f"  + {mod.strip()[:80]}")
if len(changes) > 10:
    print(f"  ... ({len(changes)-10} more)")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(new)
print("Saved.")
