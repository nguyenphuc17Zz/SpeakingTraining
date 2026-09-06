import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.contracts import BottleneckAnalysis
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey, MetricValue


class BottleneckAnalyzer:
    """
    Analyzes learning signals to identify the single most limiting bottleneck
    currently holding back the learner's Japanese conversational development.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def analyze_bottleneck(self, metrics: dict[str, MetricValue]) -> BottleneckAnalysis:
        """
        SOTA TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
        and Goldratt's Theory of Constraints (TOC) Sensitivity Analysis.
        Ranks candidate bottlenecks without first-match masking.
        """
        grammar_val = metrics.get(MetricKey.GRAMMAR_ACCURACY.value)
        natural_val = metrics.get(MetricKey.NATURALNESS.value)
        speed_val = metrics.get(MetricKey.RESPONSE_SPEED.value)
        transfer_val = metrics.get(MetricKey.TRANSFER_RATE.value)
        mora_val = metrics.get(MetricKey.MORA_TIMING.value)
        exercise_succ = metrics.get(MetricKey.EXERCISE_SUCCESS_RATE.value)

        g_score = grammar_val.value if grammar_val else 75.0
        n_score = natural_val.value if natural_val else 70.0
        speed_ms = speed_val.value if speed_val else 1200.0
        transfer_pct = transfer_val.value if transfer_val else 60.0
        mora_score = mora_val.value if mora_val else 75.0
        drill_succ = exercise_succ.value if exercise_succ else 70.0

        # Sample sizes for evidence weighting
        g_n = grammar_val.sample_size if grammar_val else 3
        n_n = natural_val.sample_size if natural_val else 3
        s_n = speed_val.sample_size if speed_val else 3
        t_n = transfer_val.sample_size if transfer_val else 3
        m_n = mora_val.sample_size if mora_val else 3

        # Define candidate specs: (candidate_key, label, desc, focus, target_gap, sample_n, toc_sensitivity, evidence_str)
        candidates: list[dict[str, Any]] = []

        # 1. Spontaneous Transfer Gap
        # Drill success is high (>75) but transfer into free speech is lagging
        transfer_gap = max(0.0, drill_succ - transfer_pct) if drill_succ >= 75.0 else 0.0
        candidates.append({
            "key": "transfer_gap",
            "candidate": "Spontaneous Transfer Gap (自由発話への定着)",
            "description": "Bạn nắm rất chắc cấu trúc trong bài tập và drill, nhưng chưa phản xạ tự nhiên trong hội thoại tự do. Kiến thức ngữ pháp không thiếu — cần chuyển trọng tâm sang roleplay thực chiến.",
            "suggested_focus": "Spontaneous roleplay & free conversation",
            "gap": transfer_gap,
            "sample_n": t_n,
            "toc_multiplier": 1.45,  # High systemic bottleneck: knowledge blocked from usage
            "evidence": f"Exercise success: {drill_succ}% vs Spontaneous transfer: {transfer_pct}%",
        })

        # 2. Grammar Production
        grammar_gap = max(0.0, 80.0 - g_score)
        candidates.append({
            "key": "grammar_production",
            "candidate": "Grammar Production (文法・助詞の運用力)",
            "description": "Lỗi trợ từ và chia động từ còn xuất hiện thường xuyên, làm gián đoạn mạch diễn đạt. Hãy củng cố các mẫu ngữ pháp cơ bản trước khi tăng tốc độ hội thoại.",
            "suggested_focus": "Targeted grammar & particle drills",
            "gap": grammar_gap,
            "sample_n": g_n,
            "toc_multiplier": 1.35,  # High structural bottleneck: structural errors degrade message clarity
            "evidence": f"Grammar accuracy: {g_score}%",
        })

        # 3. Response Latency
        latency_gap = max(0.0, (speed_ms - 1500.0) / 25.0)  # each 25ms over 1.5s = 1 gap point
        candidates.append({
            "key": "latency_hesitation",
            "candidate": "Response Latency & Retrieval Speed (発話初動速度・瞬発力)",
            "description": "Ngữ pháp của bạn khá chuẩn, nhưng thời gian suy nghĩ và tìm từ trước khi mở lời còn cao (>1.8s). Vấn đề là phản xạ truy xuất từ vựng dưới áp lực thời gian.",
            "suggested_focus": "Timed response drills & speed sparring",
            "gap": latency_gap,
            "sample_n": s_n,
            "toc_multiplier": 1.25,  # Conversational turn-taking bottleneck
            "evidence": f"Grammar: {g_score}%, Average response latency: {speed_ms}ms",
        })

        # 4. Naturalness & Pragmatic Nuance
        natural_gap = max(0.0, 80.0 - n_score)
        candidates.append({
            "key": "naturalness_nuance",
            "candidate": "Naturalness & Pragmatic Nuance (表現の自然さ・敬語ニュアンス)",
            "description": "Câu nói của bạn đúng ngữ pháp nhưng còn mang tính dịch từ (literal translation) hoặc thiếu đuôi câu tự nhiên (ね・よ) và chuyển đổi kính ngữ phù hợp ngữ cảnh.",
            "suggested_focus": "Casual conversation & native phrase shadowing",
            "gap": natural_gap,
            "sample_n": n_n,
            "toc_multiplier": 1.10,  # Pragmatic refinement
            "evidence": f"Grammar accuracy: {g_score}% vs Naturalness: {n_score}%",
        })

        # 5. Mora Timing & Rhythm
        mora_gap = max(0.0, 75.0 - mora_score)
        candidates.append({
            "key": "mora_rhythm",
            "candidate": "Mora Timing & Rhythm (拍感覚・促音・長音)",
            "description": "Khoảng cách trường âm và âm ngắt (sokuon) chưa chuẩn nhịp tiếng Nhật, khiến người nghe bản xứ cảm thấy ngắt quãng.",
            "suggested_focus": "Mora timing & YouTube shadowing",
            "gap": mora_gap,
            "sample_n": m_n,
            "toc_multiplier": 1.05,  # Acoustic prosody
            "evidence": f"Mora rhythm accuracy: {mora_score}%",
        })

        # Check if all gaps are negligible (Balanced Progression)
        max_gap = max(c["gap"] for c in candidates)
        if max_gap < 12.0:
            return BottleneckAnalysis(
                candidate="Balanced Development (バランス良好)",
                confidence=ConfidenceLevel.HIGH,
                description="Các kỹ năng đang phát triển đồng đều. Hãy tiếp tục duy trì nhịp độ luyện tập đa dạng giữa hội thoại và shadowing.",
                evidence_keys=["All dimensions within normal progress thresholds"],
                suggested_focus="Maintain daily practice routine",
                ranking_score=1.0,
                secondary_bottlenecks=[],
            )

        # Build TOPSIS Decision Matrix: [m candidates x 3 criteria]
        # Criteria: [Severity Gap (C1), Sample Evidence (C2), TOC Throughput Multiplier (C3)]
        import math
        weights = [0.45, 0.20, 0.35]
        m = len(candidates)
        raw_matrix = []
        for c in candidates:
            # Normalize sample confidence [0.3 to 1.0]
            conf_norm = min(1.0, float(c["sample_n"]) / (float(c["sample_n"]) + 3.0))
            raw_matrix.append([float(c["gap"]), conf_norm, float(c["toc_multiplier"])])

        # Normalize columns (Euclidean norm)
        col_norms = [
            math.sqrt(sum(raw_matrix[i][j] ** 2 for i in range(m))) + 1e-9
            for j in range(3)
        ]
        norm_matrix = [
            [raw_matrix[i][j] / col_norms[j] for j in range(3)]
            for i in range(m)
        ]

        # Apply weights
        weighted_matrix = [
            [norm_matrix[i][j] * weights[j] for j in range(3)]
            for i in range(m)
        ]

        # Ideal Positive (A+) and Ideal Negative (A-)
        ideal_pos = [max(weighted_matrix[i][j] for i in range(m)) for j in range(3)]
        ideal_neg = [min(weighted_matrix[i][j] for i in range(m)) for j in range(3)]

        # Closeness calculation
        topsis_scores = []
        for i in range(m):
            d_pos = math.sqrt(sum((weighted_matrix[i][j] - ideal_pos[j]) ** 2 for j in range(3)))
            d_neg = math.sqrt(sum((weighted_matrix[i][j] - ideal_neg[j]) ** 2 for j in range(3)))
            c_score = d_neg / max(1e-9, (d_pos + d_neg))
            topsis_scores.append(round(c_score, 3))
            candidates[i]["closeness"] = c_score

        # Rank candidates by closeness descending
        ranked_indices = sorted(range(m), key=lambda idx: topsis_scores[idx], reverse=True)
        top_idx = ranked_indices[0]
        top_candidate = candidates[top_idx]

        # Determine confidence of the primary candidate
        conf = ConfidenceLevel.HIGH if top_candidate["sample_n"] >= 4 else ConfidenceLevel.MEDIUM

        secondary = []
        for idx in ranked_indices[1:]:
            cand = candidates[idx]
            if cand["closeness"] >= 0.30 and cand["gap"] >= 10.0:
                secondary.append({
                    "candidate": cand["candidate"],
                    "ranking_score": round(cand["closeness"], 2),
                    "evidence": cand["evidence"],
                })

        return BottleneckAnalysis(
            candidate=top_candidate["candidate"],
            confidence=conf,
            description=top_candidate["description"],
            evidence_keys=[top_candidate["evidence"]],
            suggested_focus=top_candidate["suggested_focus"],
            ranking_score=round(top_candidate["closeness"], 2),
            secondary_bottlenecks=secondary,
        )
