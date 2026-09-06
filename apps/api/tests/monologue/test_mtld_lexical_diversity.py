import pytest
from app.domains.monologue.analytics.lexical_profiler import LexicalProfiler


def test_mtld_diverse_vs_repetitive():
    """Verify MTLD gives high score for rich varied speech and low score for repetitive speech."""
    lp = LexicalProfiler(provider=None)

    # Repetitive speech: repeating the same 3 words
    repetitive_tokens = ["これ", "は", "本", "です"] * 10
    mtld_rep = lp.compute_mtld(repetitive_tokens)
    hdd_rep = lp.compute_hdd(repetitive_tokens)

    # Rich speech: diverse vocabulary
    rich_tokens = [
        "日本", "の", "四季", "は", "美しく", "春", "には", "桜", "が", "咲き誇り",
        "夏", "には", "青空", "と", "入道雲", "が", "広がり", "秋", "には", "紅葉",
        "が", "山々", "を", "彩り", "冬", "には", "白雪", "が", "街", "を",
        "静かに", "包み込み", "ます", "伝統", "文化", "も", "非常に", "豊か", "です"
    ]
    mtld_rich = lp.compute_mtld(rich_tokens)
    hdd_rich = lp.compute_hdd(rich_tokens)

    assert mtld_rich > mtld_rep
    assert hdd_rich > hdd_rep
    assert mtld_rep < 25.0
    assert mtld_rich > 20.0


def test_lexical_profiler_mtld_integration():
    """Verify LexicalProfiler.analyze returns mtld, hdd, and lexical_diversity_rating."""
    lp = LexicalProfiler(provider=None)
    transcript = "今日は天気がとても良いので、近所の公園を散歩しました。風が心地よかったです。"
    res = lp.analyze(transcript)

    assert "mtld" in res
    assert "hdd" in res
    assert "lexical_diversity_rating" in res
    assert res["mtld"] >= 0.0
    assert 0.0 <= res["hdd"] <= 1.0
    assert res["lexical_diversity_rating"] in ("rich", "moderate", "basic", "repetitive")
