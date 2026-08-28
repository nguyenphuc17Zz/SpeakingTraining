"""DoubleKeigoAnalyzer — nuanced classification, not binary."""

from __future__ import annotations

import re


# Established double keigo that is accepted (even if technically double)
ACCEPTED_ESTABLISHED = {
    "お召し上がりになる",
    "お休みになる",
    "ご覧になる",
    "お目にかかる",
    "お伺いする",
}

# Nonstandard / discouraged
NONSTANDARD_PATTERNS = [
    r"お.*になられる",  # お書きになられる (sonkeigo + reru double)
    r"ご.*になられる",
    r"お.*される",
]


class DoubleKeigoAnalyzer:
    def analyze(self, text: str) -> dict:
        # Check if text contains multiple honorific morphemes suspiciously
        # Simple heuristic: count honorific markers
        markers = 0
        markers += text.count("お")
        markers += text.count("ご")
        markers += text.count("に") if "になる" in text else 0
        markers += text.count("られる") if "られる" in text else 0
        markers += text.count("される") if "される" in text else 0

        if text in ACCEPTED_ESTABLISHED:
            return {"category": "double_keigo", "status": "accepted_established", "severity": "none", "confidence": 0.98}
        for pat in NONSTANDARD_PATTERNS:
            if re.search(pat, text):
                return {"category": "double_keigo", "status": "generally_inappropriate", "severity": "major", "confidence": 0.92}
        if markers >= 3 and "お" in text and "になる" in text:
            # Could be borderline
            return {"category": "double_keigo", "status": "context_dependent", "severity": "minor", "confidence": 0.6}
        if markers >= 4:
            return {"category": "double_keigo", "status": "generally_inappropriate", "severity": "major", "confidence": 0.85}
        return {"category": "double_keigo", "status": "accepted_established", "severity": "none", "confidence": 0.7}
