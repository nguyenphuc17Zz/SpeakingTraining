"""SpeechVarietyPolicy — SHA256 anti-repetition (§8)."""

from __future__ import annotations

import hashlib
import re


class SpeechVarietyPolicy:
    @staticmethod
    def normalize_topic(text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[。！？、\s\!\?\,\.]+$", "", t)
        return t

    @classmethod
    def compute_signature(
        cls,
        normalized_topic: str,
        genre: str,
        topic_domain: str,
        difficulty: int,
        duration_sec: int,
        constraint_sig: str | None = None,
    ) -> str:
        raw = f"{cls.normalize_topic(normalized_topic)}|{genre.lower()}|{topic_domain.lower()}|{difficulty}|{duration_sec}|{constraint_sig or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def is_duplicate(
        cls,
        signature: str,
        recent_signatures: list[str],
        window: int = 20,
    ) -> bool:
        return signature in (recent_signatures or [])[-window:]

    @classmethod
    def is_near_duplicate_topic(
        cls,
        topic: str,
        recent_topics: list[str],
        threshold: float = 0.75,
    ) -> bool:
        # Jaccard on token sets — support Japanese
        def tokens(s: str) -> set[str]:
            return set(re.findall(r"[ぁ-んァ-ン一-龯a-zA-Z0-9_]+", s.lower()))

        t_set = tokens(topic)
        if not t_set:
            return False
        for rt in recent_topics or []:
            r_set = tokens(rt)
            if not r_set:
                continue
            jaccard = len(t_set & r_set) / max(1, len(t_set | r_set))
            if jaccard >= threshold:
                return True
        return False
