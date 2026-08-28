# External Linguistic Resources

| Resource | Version | License | Source | Purpose | Redistribution | Purpose in App |
|----------|---------|---------|--------|---------|----------------|----------------|
| SudachiPy + sudachidict_core | 0.6.11 / 20260723 | Apache 2.0 | https://github.com/WorksApplications/SudachiPy | Word segmentation, lemma, POS, reading | Allowed | Primary morphology, reading resolver fallback |
| pykakasi | 2.2.0 | GPL-3.0 / Apache 2.0 (kanwadict) | https://github.com/miurahr/pykakasi | Kana conversion | Allowed | Fallback reading when Sudachi fails |
| pyopenjtalk | 0.3.x | Modified BSD | https://github.com/r9y9/pyopenjtalk (HTS/OpenJTalk) | G2P, mora, accent kernel, full-context label | BSD, allow commercial with attribution | Pitch-accent provider (primary for Mode 3) |
| librosa | 0.10+ | ISC | https://librosa.org | pyin F0, spectral | Allowed | Primary F0 pyin |
| praat-parselmouth | 0.4+ | GPL-3.0 / BSD (Praat) | https://github.com/YannickJadoul/Parselmouth | Praat to_pitch, formant | GPL, allow | Secondary F0 cross-check |
| WhisperX / faster-whisper | 1.0+ | MIT / Apache | https://github.com/m-bain/whisperX | Forced alignment per mora | MIT | Mora alignment WhisperX |
| wordfreq | 3.x | MIT | https://github.com/rspeer/wordfreq | Frequency lookup | MIT | Corpus frequency (optional) |
| jamdict/JMDict | - | CC BY-SA 3.0 | https://www.edrdg.org/jmdict/ | Lexical gloss with keigo tags | CC BY-SA, attribution required | Keigo lexical provider (optional) |
| VOICEVOX Engine | - | GPL-3.0 | https://voicevox.hiroshiba.jp | TTS reference audio | GPL | Reference audio synthesis |

> App supports replacing any resource without rewriting Mode 3 via provider interfaces `JapanesePitchResourceProvider`, `JapaneseLanguageResourceProvider`.
