import pytest
from app.domains.pronunciation.contracts import PitchAccentPattern
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.pitch_accent_resolver import PitchAccentTargetResolver
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver


def test_reading_resolver_kanji_and_kana():
    # Kanji to Hiragana
    hira1 = JapaneseReadingResolver.to_hiragana("学校")
    assert hira1 == "がっこう"

    hira2 = JapaneseReadingResolver.to_hiragana("新聞")
    assert hira2 == "しんぶん"

    hira3 = JapaneseReadingResolver.to_hiragana("映画を見ました")
    assert "えいが" in hira3
    assert "みました" in hira3

    # Katakana conversion
    hira_kata = JapaneseReadingResolver.to_hiragana("コーヒー")
    assert hira_kata == "こーひー"


def test_mora_segmentation_gakkou():
    # がっこう -> 4 morae: が, っ, こ, う
    moras = JapaneseMoraAnalyzer.segment_moras("がっこう")
    assert len(moras) == 4
    assert [m.kana for m in moras] == ["が", "っ", "こ", "う"]
    assert moras[1].is_special is True
    assert moras[1].special_type == "gemination"  # っ
    assert moras[3].is_special is True
    assert moras[3].special_type == "long_vowel"   # う extends こ


def test_mora_segmentation_obasan_vs_obaasan():
    # おばさん -> 4 morae: お, ば, さ, ん
    m_short = JapaneseMoraAnalyzer.segment_moras("おばさん")
    assert len(m_short) == 4
    assert [m.kana for m in m_short] == ["お", "ば", "さ", "ん"]
    assert m_short[3].special_type == "nasal"

    # おばあさん -> 5 morae: お, ば, あ, さ, ん
    m_long = JapaneseMoraAnalyzer.segment_moras("おばあさん")
    assert len(m_long) == 5
    assert [m.kana for m in m_long] == ["お", "ば", "あ", "さ", "ん"]
    assert m_long[2].is_special is True
    assert m_long[2].special_type == "long_vowel"


def test_mora_segmentation_yoon_contracted():
    # きょうは映画 (kyou wa eiga) -> きょう: きょ(1 mora), う(1 mora)
    moras = JapaneseMoraAnalyzer.segment_moras("きょう")
    assert len(moras) == 2
    assert moras[0].kana == "きょ"
    assert moras[0].is_special is True
    assert moras[0].special_type == "contracted"
    assert moras[1].kana == "う"
    assert moras[1].special_type == "long_vowel"


def test_mora_segmentation_sokuon_kitte_vs_kite():
    # きて -> 2 morae
    m_kite = JapaneseMoraAnalyzer.segment_moras("きて")
    assert len(m_kite) == 2

    # きって -> 3 morae: き, っ, て
    m_kitte = JapaneseMoraAnalyzer.segment_moras("きって")
    assert len(m_kitte) == 3
    assert m_kitte[1].kana == "っ"
    assert m_kitte[1].special_type == "gemination"


def test_pitch_accent_target_resolver():
    # 雨 (rain) -> Atamadaka (1) [H, L]
    pat_ame, kernel_ame, levels_ame = PitchAccentTargetResolver.resolve_target("あめ")
    assert pat_ame == PitchAccentPattern.ATAMADAKA
    assert kernel_ame == 1
    assert levels_ame == ["H", "L"]

    # 学校 (school) -> Heiban (0) [L, H, H, H]
    pat_gak, kernel_gak, levels_gak = PitchAccentTargetResolver.resolve_target("がっこう")
    assert pat_gak == PitchAccentPattern.HEIBAN
    assert kernel_gak == 0
    assert levels_gak == ["L", "H", "H", "H"]

    # 先生 (teacher) -> Nakadaka (3) [L, H, H, L]
    pat_sen, kernel_sen, levels_sen = PitchAccentTargetResolver.resolve_target("せんせい")
    assert pat_sen == PitchAccentPattern.NAKADAKA
    assert kernel_sen == 3
    assert levels_sen == ["L", "H", "H", "L"]
