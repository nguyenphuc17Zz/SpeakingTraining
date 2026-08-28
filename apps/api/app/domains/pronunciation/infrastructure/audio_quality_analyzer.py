import numpy as np

from app.domains.pronunciation.contracts import AudioQualityReport
from app.domains.pronunciation.infrastructure.vad_analyzer import VADAnalyzer


class AudioQualityAnalyzer:
    """Validates raw audio quality (signal level, clipping, SNR, silence, duration) before pronunciation analysis."""

    MIN_DURATION_MS = 250       # At least 250ms
    MAX_DURATION_MS = 60000     # 60s max
    MIN_RMS = 0.003             # Threshold for "Too Quiet"
    CLIPPING_THRESHOLD = 0.99   # Sample near max peak
    MAX_CLIPPING_RATIO = 0.08   # Over 8% clipping is severely distorted

    @classmethod
    def analyze_quality(cls, samples: np.ndarray, sample_rate: int = 16000) -> AudioQualityReport:
        """Evaluates whether recording is usable for phonetic/pitch analysis."""
        if len(samples) == 0:
            return AudioQualityReport(
                is_usable=False,
                signal_level_rms=0.0,
                is_clipped=False,
                snr_estimate_db=0.0,
                silence_ratio=1.0,
                duration_ms=0,
                issues=["Audio recording is empty or unreadable."],
                guidance="Vui lòng kiểm tra lại micro và thử thu âm lại.",
            )

        duration_ms = int((len(samples) / float(sample_rate)) * 1000)
        rms = float(np.sqrt(np.mean(samples**2)))
        peak = float(np.max(np.abs(samples)))

        # Clipping analysis
        clipped_samples = np.sum(np.abs(samples) >= cls.CLIPPING_THRESHOLD)
        clipping_ratio = float(clipped_samples / len(samples))
        is_severely_clipped = clipping_ratio > cls.MAX_CLIPPING_RATIO

        # VAD Analysis
        vad_info = VADAnalyzer.analyze(samples, sample_rate)
        silence_ratio = vad_info["silence_ratio"]
        speech_ms = vad_info["total_speech_ms"]

        # Approximate SNR estimate (dB)
        # Ratio of top 20% highest energy frames to bottom 20% lowest energy frames
        snr_db = cls._estimate_snr(samples, sample_rate)

        issues = []
        is_usable = True
        guidance = None

        if duration_ms < cls.MIN_DURATION_MS:
            issues.append("Bản thu âm quá ngắn (dưới 0.25 giây).")
            is_usable = False
            guidance = "Bản thu âm quá ngắn. Vui lòng phát âm trọn vẹn từ hoặc câu."

        if rms < cls.MIN_RMS or speech_ms < 150:
            issues.append("Âm lượng quá nhỏ hoặc không phát hiện tiếng nói rõ ràng.")
            is_usable = False
            guidance = "Âm lượng quá nhỏ. Vui lòng nói gần micro hơn hoặc tăng độ nhạy micro."

        if is_severely_clipped:
            issues.append("Âm thanh bị méo/rè do âm lượng vượt quá ngưỡng (clipping).")
            guidance = "Âm thanh hơi to và bị rè. Hãy giảm nhẹ âm lượng hoặc đưa micro ra xa hơn một chút."

        if silence_ratio > 0.85 and duration_ms > 2000:
            issues.append("Tỷ lệ khoảng lặng quá cao so với giọng nói.")
            guidance = "Bản thu có nhiều khoảng trống. Hãy bắt đầu nói ngay khi bấm nút thu âm."

        if snr_db is not None and snr_db < 5.0 and len(issues) == 0:
            issues.append("Môi trường có nhiều tạp âm nền.")
            guidance = "Phát hiện tiếng ồn xung quanh. Kết quả phân tích có thể giảm độ chính xác."

        return AudioQualityReport(
            is_usable=is_usable,
            signal_level_rms=round(rms, 4),
            is_clipped=is_severely_clipped,
            snr_estimate_db=round(snr_db, 1) if snr_db is not None else None,
            silence_ratio=silence_ratio,
            duration_ms=duration_ms,
            issues=issues,
            guidance=guidance,
        )

    @classmethod
    def _estimate_snr(cls, samples: np.ndarray, sample_rate: int) -> float | None:
        """Estimates Signal-to-Noise Ratio (dB) using frame-level RMS percentiles."""
        frame_size = int(sample_rate * 0.02)
        if len(samples) < frame_size * 5:
            return None

        num_frames = len(samples) // frame_size
        energies = [
            float(np.sqrt(np.mean(samples[f * frame_size : (f + 1) * frame_size] ** 2)))
            for f in range(num_frames)
        ]

        if not energies:
            return None

        energies.sort()
        noise_floor = np.mean(energies[: max(1, len(energies) // 5)]) + 1e-6
        signal_peak = np.mean(energies[-max(1, len(energies) // 5) :]) + 1e-6

        snr = 20.0 * np.log10(signal_peak / noise_floor)
        return float(snr)
