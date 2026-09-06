"""Vowel Formant & Articulation Space Analyzer.

SOTA Acoustic Phonetics & Speech DSP Engine:
1. Linear Predictive Coding (LPC) Formant Extraction via Levinson-Durbin Recursion and Polynomial Root Decomposition.
2. Vowel Space Area (VSA) computation using Gauss's Shoelace Area Formula across Japanese cardinal vowels (/a, i, u, e, o/).
3. Formant Centralization Ratio (FCR) (Sapir et al., 2010; Vorperian & Kent, 2007) for acoustic vowel dispersion and articulation crispness.
4. Japanese High Vowel Devoicing (無声化) detection for /i, u/ in unvoiced phonological environments (e.g., です, すき, したい).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class FormantMeasurement:
    """Acoustic formant measurement for a single vowel instance."""

    vowel: str
    f1_hz: float
    f2_hz: float
    f3_hz: float | None = None
    bandwidth_hz: float | None = None
    is_devoiced: bool = False
    confidence: float = 1.0


@dataclass
class VowelSpaceAssessment:
    """Comprehensive acoustic vowel space & articulation quality assessment."""

    vsa_hz2: float
    fcr: float
    articulation_clarity_score: float
    vowel_dispersion_status: str  # "expanded_crisp", "natural", "mild_centralization", "compressed_slurred"
    devoiced_moras_detected: list[str] = field(default_factory=list)
    vowel_formants: dict[str, tuple[float, float]] = field(default_factory=dict)
    feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vsa_hz2": round(self.vsa_hz2, 1),
            "fcr": round(self.fcr, 3),
            "articulation_clarity_score": round(self.articulation_clarity_score, 1),
            "vowel_dispersion_status": self.vowel_dispersion_status,
            "devoiced_moras_detected": self.devoiced_moras_detected,
            "vowel_formants": {k: (round(v[0], 1), round(v[1], 1)) for k, v in self.vowel_formants.items()},
            "feedback": self.feedback,
        }


class VowelFormantAnalyzer:
    """Acoustic vowel space & formant centralization analyzer for Japanese phonetics."""

    # Reference Japanese vowel formants (Acoustic Phonetics standards for Tokyo Japanese)
    # Formants (F1, F2) in Hz
    REFERENCE_FORMANTS: dict[str, tuple[float, float]] = {
        "a": (780.0, 1250.0),
        "i": (280.0, 2350.0),
        "u": (360.0, 1320.0),  # [ɯᵝ] unrounded/compressed high-back
        "e": (520.0, 1900.0),
        "o": (490.0, 950.0),
    }

    # Standard Japanese devoicing environments (consonant + high vowel /i, u/ + consonant/end)
    # Voiceless consonants in Japanese: k, s, sh, t, ch, ts, h, f, p
    DEVOICING_KANA = {
        "き", "く", "し", "す", "ち", "つ", "ひ", "ふ", "ぴ", "ぷ",
        "キ", "ク", "シ", "ス", "チ", "ツ", "ヒ", "フ", "ピ", "プ",
    }

    @classmethod
    def levinson_durbin(cls, r: np.ndarray, order: int) -> tuple[np.ndarray, float]:
        """Solves Toeplitz system R * a = r for LPC coefficients using Levinson-Durbin recursion.

        Args:
            r: Autocorrelation coefficients of length >= order + 1.
            order: Prediction order P.

        Returns:
            a: LPC filter coefficients [1.0, a_1, ..., a_P].
            error: Residual error energy.
        """
        if len(r) <= order:
            raise ValueError(f"Autocorrelation array length {len(r)} must be > order {order}")

        a = np.zeros(order + 1, dtype=np.float64)
        a[0] = 1.0
        error = float(r[0])

        if error <= 1e-12:
            return a, 0.0

        for i in range(1, order + 1):
            # Reflection coefficient
            acc = sum(a[j] * r[i - j] for j in range(1, i))
            k = -(r[i] + acc) / error
            if abs(k) >= 1.0:
                # Clamp to maintain filter stability
                k = 0.999 * np.sign(k)

            # Update predictor coefficients
            a_prev = a.copy()
            a[i] = k
            for j in range(1, i):
                a[j] = a_prev[j] + k * a_prev[i - j]

            error *= 1.0 - k * k
            if error <= 0:
                break

        return a, float(error)

    @classmethod
    def extract_lpc_formants(
        cls,
        signal: np.ndarray,
        sample_rate: int = 16000,
        order: int | None = None,
        max_formants: int = 4,
    ) -> list[tuple[float, float]]:
        """Extracts candidate formants (frequency_hz, bandwidth_hz) from an audio frame using LPC.

        Args:
            signal: 1D float numpy array of audio samples (e.g. 20-40ms).
            sample_rate: Sample rate in Hz (default 16000).
            order: LPC order (if None, defaults to 2 + sample_rate // 1000).
            max_formants: Maximum number of formant candidates to return.

        Returns:
            List of (frequency_hz, bandwidth_hz) sorted by frequency.
        """
        if len(signal) < 32:
            return []

        if order is None:
            order = 2 + sample_rate // 1000  # e.g., 18 for 16kHz

        # 1. Pre-emphasis filter to boost high frequency spectral peaks: y[n] = x[n] - 0.97 x[n-1]
        pre_emphasized = np.append(signal[0], signal[1:] - 0.97 * signal[:-1])

        # 2. Hamming windowing
        window = np.hamming(len(pre_emphasized))
        windowed = pre_emphasized * window

        # 3. Autocorrelation
        n = len(windowed)
        autocorr = np.correlate(windowed, windowed, mode="full")
        r = autocorr[n - 1 : n + order]

        if r[0] <= 1e-10:
            return []

        # 4. Levinson-Durbin
        a, err = cls.levinson_durbin(r, order)

        # 5. Root finding of prediction polynomial A(z)
        roots = np.roots(a)

        # 6. Extract conjugate poles with positive imaginary part
        formant_candidates = []
        for root in roots:
            if np.imag(root) > 0.01:
                freq = float(np.arctan2(np.imag(root), np.real(root)) * (sample_rate / (2.0 * np.pi)))
                bandwidth = float(-np.log(max(1e-6, np.abs(root))) * (sample_rate / np.pi))

                # Physical plausibility filter for human vocal tract
                if 180.0 <= freq <= 4000.0 and bandwidth < 650.0:
                    formant_candidates.append((freq, bandwidth))

        # Sort by frequency
        formant_candidates.sort(key=lambda x: x[0])
        return formant_candidates[:max_formants]

    @classmethod
    def calculate_vowel_space_area(cls, vowel_coords: dict[str, tuple[float, float]]) -> float:
        """Calculates Vowel Space Area (VSA) in Hz^2 using Gauss's Shoelace Formula.

        Polygon order for Japanese 5 vowels:
        /i/ (Front-High) -> /e/ (Front-Mid) -> /a/ (Low) -> /o/ (Back-Mid) -> /u/ (Back-High)
        """
        required_vowels = ["i", "e", "a", "o", "u"]
        # If any vowel is missing, interpolate from reference
        polygon_points: list[tuple[float, float]] = []
        for v in required_vowels:
            if v in vowel_coords:
                polygon_points.append(vowel_coords[v])
            else:
                polygon_points.append(cls.REFERENCE_FORMANTS[v])

        n = len(polygon_points)
        if n < 3:
            return 0.0

        # Shoelace formula: Area = 0.5 * |sum(x_i * y_{i+1} - x_{i+1} * y_i)|
        # Here x = F2 (backness/frontness axis), y = F1 (vowel height axis)
        area_sum = 0.0
        for i in range(n):
            x_i, y_i = polygon_points[i][1], polygon_points[i][0]  # (F2, F1)
            next_idx = (i + 1) % n
            x_next, y_next = polygon_points[next_idx][1], polygon_points[next_idx][0]
            area_sum += (x_i * y_next) - (x_next * y_i)

        return float(abs(area_sum) * 0.5)

    @classmethod
    def calculate_formant_centralization_ratio(cls, vowel_coords: dict[str, tuple[float, float]]) -> float:
        """Calculates Formant Centralization Ratio (FCR) (Sapir et al., 2010).

        Formula:
            FCR = (F2_u + F2_a + F1_i + F1_u) / (F2_i + F1_a)

        Properties:
            - Decreases as vowel space expands (clear articulation).
            - FCR <= 1.0 indicates clear, expanded articulation contrast.
            - FCR > 1.05 indicates vowel centralization / muddled speech.
        """
        coords = {k: vowel_coords.get(k, cls.REFERENCE_FORMANTS[k]) for k in ("a", "i", "u")}

        f1_a, f2_a = coords["a"]
        f1_i, f2_i = coords["i"]
        f1_u, f2_u = coords["u"]

        numerator = f2_u + f2_a + f1_i + f1_u
        denominator = f2_i + f1_a

        if denominator <= 1e-6:
            return 1.0

        return float(numerator / denominator)

    @classmethod
    def detect_devoicing_environment(
        cls,
        mora_kana: str,
        is_voiced_acoustic: bool,
        is_phrase_final: bool = False,
    ) -> bool:
        """Determines if an unvoiced mora is a legitimate Japanese phonological devoicing (無声化).

        E.g. す in です, き in すき, し in したい.
        """
        clean_kana = mora_kana.strip()
        if clean_kana in cls.DEVOICING_KANA:
            if not is_voiced_acoustic or is_phrase_final:
                return True
        return False

    @classmethod
    def assess_vowel_space(
        cls,
        measured_vowels: dict[str, tuple[float, float]],
        detected_moras: list[str] | None = None,
    ) -> VowelSpaceAssessment:
        """Performs end-to-end evaluation of Japanese vowel space area and articulation clarity."""
        vsa = cls.calculate_vowel_space_area(measured_vowels)
        fcr = cls.calculate_formant_centralization_ratio(measured_vowels)

        # Baseline reference Japanese VSA
        ref_vsa = cls.calculate_vowel_space_area(cls.REFERENCE_FORMANTS)

        # Articulation Clarity Score (0 - 100)
        vsa_ratio = min(1.3, max(0.5, vsa / max(1.0, ref_vsa)))
        fcr_penalty = max(0.0, (fcr - 1.0) * 120.0)

        raw_score = (vsa_ratio * 80.0) + (20.0 - fcr_penalty)
        score = float(np.clip(raw_score, 40.0, 98.0))

        if fcr <= 0.96 and vsa >= ref_vsa * 0.95:
            status = "expanded_crisp"
            feedback = "Khẩu hình các nguyên âm mở rất rõ nét và phân tách rành mạch (Expanded Vowel Space)."
        elif fcr <= 1.04:
            status = "natural"
            feedback = "Khẩu hình các nguyên âm phát âm tự nhiên theo chuẩn tiếng Nhật Tokyo."
        elif fcr <= 1.12:
            status = "mild_centralization"
            feedback = "Có hiện tượng khép khẩu hình nhẹ (Mild Centralization). Hãy mở rõ hơn nguyên âm /a/ và đưa lưỡi sâu cho /u/."
        else:
            status = "compressed_slurred"
            feedback = "Các nguyên âm bị dính âm, khẩu hình quá hẹp (Centralized Articulation). Hãy chú ý phân biệt rõ giữa /i/, /e/ và /u/."

        devoiced: list[str] = []
        if detected_moras:
            for mora in detected_moras:
                if mora in cls.DEVOICING_KANA:
                    devoiced.append(mora)

        return VowelSpaceAssessment(
            vsa_hz2=vsa,
            fcr=fcr,
            articulation_clarity_score=score,
            vowel_dispersion_status=status,
            devoiced_moras_detected=devoiced,
            vowel_formants=measured_vowels,
            feedback=feedback,
        )
