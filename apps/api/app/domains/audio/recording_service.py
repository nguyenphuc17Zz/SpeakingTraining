import io
import math
import wave

import numpy as np

from app.core.logging import logger
from app.domains.audio.contracts import AudioQualityReport, AudioQualityStatus


class AudioQualityAnalyzer:
    """
    Analyzes microphone recording quality, checking volume levels, noise floors, and clipping distortion.
    """

    @classmethod
    def analyze(cls, audio_bytes: bytes) -> AudioQualityReport:
        if not audio_bytes or len(audio_bytes) < 44:
            return AudioQualityReport(
                volume_rms=0.0,
                volume_db=-90.0,
                noise_level_db=-90.0,
                snr_db=0.0,
                has_clipping=False,
                clipping_samples_count=0,
                duration_ms=0,
                quality=AudioQualityStatus.SILENT,
                recommendation="Không có dữ liệu âm thanh ghi nhận được. Hãy kiểm tra lại kết nối micro.",
                warnings=["Dữ liệu âm thanh trống hoặc quá ngắn."],
            )

        try:
            # Parse WAV bytes
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                num_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                num_frames = wf.getnframes()
                raw_frames = wf.readframes(num_frames)

            # Convert to numpy array based on sample width
            if sample_width == 2:  # 16-bit PCM
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 1:  # 8-bit PCM
                samples = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif sample_width == 4:  # 32-bit float or int
                samples = np.frombuffer(raw_frames, dtype=np.float32)
            else:
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0

            if num_channels > 1:
                # Average channels to mono
                samples = samples.reshape(-1, num_channels).mean(axis=1)

            duration_ms = int((num_frames / framerate) * 1000) if framerate > 0 else 0

        except Exception as e:
            logger.warning(f"[AudioQualityAnalyzer] WAV parsing fallback: {e}")
            # Fallback estimation for raw audio chunk
            samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            duration_ms = int((len(samples) / 16000.0) * 1000)

        if len(samples) == 0:
            return AudioQualityReport(
                volume_rms=0.0,
                volume_db=-90.0,
                noise_level_db=-90.0,
                snr_db=0.0,
                has_clipping=False,
                clipping_samples_count=0,
                duration_ms=duration_ms,
                quality=AudioQualityStatus.SILENT,
                recommendation="Không phát hiện âm thanh trong bản ghi.",
                warnings=["Không có mẫu sóng âm."],
            )

        # 1. Calculate RMS & Volume in dB
        rms = float(np.sqrt(np.mean(samples ** 2)))
        volume_db = 20.0 * math.log10(max(rms, 1e-5))

        # 2. Clipping detection (samples with magnitude > 0.98)
        clipping_mask = np.abs(samples) >= 0.98
        clipping_count = int(np.sum(clipping_mask))
        has_clipping = clipping_count > (0.005 * len(samples))  # > 0.5% samples clipped

        # 3. Estimate noise level from quietest 10% of 50ms frames
        frame_size = int(16000 * 0.05)
        if len(samples) >= frame_size:
            num_full_frames = len(samples) // frame_size
            frame_rms_list = [
                float(np.sqrt(np.mean(samples[i * frame_size : (i + 1) * frame_size] ** 2)))
                for i in range(num_full_frames)
            ]
            sorted_rms = sorted(frame_rms_list)
            lowest_10_percent = sorted_rms[: max(1, int(len(sorted_rms) * 0.10))]
            noise_rms = float(np.mean(lowest_10_percent))
            noise_db = 20.0 * math.log10(max(noise_rms, 1e-5))
        else:
            noise_db = volume_db - 20.0

        snr_db = max(0.0, volume_db - noise_db)

        # 4. Status determination & recommendations
        warnings: list[str] = []
        if has_clipping:
            quality = AudioQualityStatus.CLIPPING
            recommendation = "Phát hiện vỡ tiếng do âm lượng quá lớn. Hãy nói xa micro hơn hoặc giảm gain của thiết bị."
            warnings.append(f"Có {clipping_count} mẫu sóng bị quá tải (clipping).")
        elif volume_db < -42.0:
            quality = AudioQualityStatus.TOO_QUIET
            recommendation = "Âm lượng thu âm quá nhỏ. Hãy nói gần micro hơn hoặc tăng độ nhạy đầu vào."
            warnings.append("Âm lượng dưới ngưỡng khuyến nghị (-42dB).")
        elif snr_db < 10.0 and volume_db > -35.0:
            quality = AudioQualityStatus.NOISY
            recommendation = "Tạp âm môi trường khá lớn. Hãy luyện tập trong không gian yên tĩnh hoặc đeo tai nghe có mic."
            warnings.append("Tỷ lệ tín hiệu trên nhiễu (SNR) thấp.")
        elif volume_db >= -30.0 and snr_db >= 18.0:
            quality = AudioQualityStatus.GOOD
            recommendation = "Chất lượng âm thanh hoàn hảo cho luyện tập hội thoại và phân tích phát âm."
        else:
            quality = AudioQualityStatus.ACCEPTABLE
            recommendation = "Chất lượng âm thanh ở mức chấp nhận được cho luyện nói."

        # 5. Otsu's Bimodal Energy VAD & Silence Trimming
        vad_res = OtsuVADTrimmer.trim_silence(samples, framerate or 16000)

        return AudioQualityReport(
            volume_rms=round(rms, 4),
            volume_db=round(volume_db, 1),
            noise_level_db=round(noise_db, 1),
            snr_db=round(snr_db, 1),
            has_clipping=has_clipping,
            clipping_samples_count=clipping_count,
            duration_ms=duration_ms,
            quality=quality,
            recommendation=recommendation,
            warnings=warnings,
            trimmed_duration_ms=vad_res.trimmed_duration_ms,
            head_silence_ms=vad_res.head_silence_ms,
            tail_silence_ms=vad_res.tail_silence_ms,
            voice_activity_ratio=vad_res.voice_activity_ratio,
        )


class VADTrimmingResult:
    """Telemetry data from Otsu's Bimodal Voice Activity Detection and Silence Trimming."""

    def __init__(
        self,
        original_duration_ms: int,
        trimmed_duration_ms: int,
        head_silence_ms: int,
        tail_silence_ms: int,
        voice_activity_ratio: float,
        optimal_threshold_db: float,
        start_sample: int = 0,
        end_sample: int = 0,
    ):
        self.original_duration_ms = original_duration_ms
        self.trimmed_duration_ms = trimmed_duration_ms
        self.head_silence_ms = head_silence_ms
        self.tail_silence_ms = tail_silence_ms
        self.voice_activity_ratio = voice_activity_ratio
        self.optimal_threshold_db = optimal_threshold_db
        self.start_sample = start_sample
        self.end_sample = end_sample


class OtsuVADTrimmer:
    """
    SOTA Otsu Global Energy Bimodal Thresholding Voice Activity Detector (VAD).
    References:
      - Otsu, N. (1979). A threshold selection method from gray-level histograms.
        IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62-66.
      - Dual-threshold hysteresis smoothing with hangover hangover padding.
    """

    FRAME_MS = 20
    HOP_MS = 10
    MIN_SPEECH_DURATION_MS = 100
    HANGOVER_FRAMES = 8
    PAD_HEAD_MS = 80
    PAD_TAIL_MS = 120

    @classmethod
    def trim_silence(cls, samples: np.ndarray, sample_rate: int = 16000) -> VADTrimmingResult:
        total_samples = len(samples)
        total_duration_ms = int((total_samples / max(1, sample_rate)) * 1000)
        if total_samples == 0 or total_duration_ms < 100:
            return VADTrimmingResult(
                original_duration_ms=total_duration_ms,
                trimmed_duration_ms=total_duration_ms,
                head_silence_ms=0,
                tail_silence_ms=0,
                voice_activity_ratio=0.0,
                optimal_threshold_db=-90.0,
                start_sample=0,
                end_sample=total_samples,
            )

        frame_len = int(sample_rate * (cls.FRAME_MS / 1000.0))
        hop_len = int(sample_rate * (cls.HOP_MS / 1000.0))
        if frame_len <= 0 or hop_len <= 0 or total_samples < frame_len:
            return VADTrimmingResult(
                original_duration_ms=total_duration_ms,
                trimmed_duration_ms=total_duration_ms,
                head_silence_ms=0,
                tail_silence_ms=0,
                voice_activity_ratio=1.0,
                optimal_threshold_db=-40.0,
                start_sample=0,
                end_sample=total_samples,
            )

        # 1. Compute frame energy in dB
        num_frames = (total_samples - frame_len) // hop_len + 1
        frame_energies_db = np.zeros(num_frames, dtype=np.float32)
        for i in range(num_frames):
            start = i * hop_len
            f = samples[start : start + frame_len]
            rms = float(np.sqrt(np.mean(f ** 2)))
            frame_energies_db[i] = 20.0 * math.log10(max(rms, 1e-5))

        # 2. Otsu's Bimodal Thresholding over Energy Histogram [-80dB, 0dB]
        min_db = -80.0
        max_db = 0.0
        num_bins = 80
        clamped_energies = np.clip(frame_energies_db, min_db, max_db)
        hist, bin_edges = np.histogram(clamped_energies, bins=num_bins, range=(min_db, max_db))
        total_p = np.sum(hist)

        if total_p == 0:
            return VADTrimmingResult(
                original_duration_ms=total_duration_ms,
                trimmed_duration_ms=total_duration_ms,
                head_silence_ms=0,
                tail_silence_ms=0,
                voice_activity_ratio=0.0,
                optimal_threshold_db=-50.0,
            )

        prob = hist.astype(np.float64) / float(total_p)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        cum_prob = np.cumsum(prob)
        cum_mean = np.cumsum(prob * bin_centers)
        global_mean = cum_mean[-1]

        variances = np.zeros(num_bins - 1, dtype=np.float64)
        for t in range(num_bins - 1):
            w0 = cum_prob[t]
            w1 = 1.0 - w0
            if w0 < 1e-5 or w1 < 1e-5:
                continue
            mu0 = cum_mean[t] / w0
            mu1 = (global_mean - cum_mean[t]) / w1
            variances[t] = w0 * w1 * ((mu0 - mu1) ** 2)

        max_var = float(np.max(variances))
        if max_var <= 1e-6:
            best_threshold_db = -45.0
        else:
            # Otsu plateau center: average of bins achieving >= 99% of max between-class variance
            plateau_mask = variances >= (0.99 * max_var)
            plateau_centers = bin_centers[:-1][plateau_mask]
            best_threshold_db = float(np.mean(plateau_centers))

        # Clamping threshold to realistic boundary
        best_threshold_db = max(-65.0, min(-28.0, best_threshold_db))
        high_threshold = best_threshold_db + 2.0
        low_threshold = best_threshold_db - 2.5

        # 3. Dual-Threshold Hysteresis with Hangover Smoothing
        speech_mask = np.zeros(num_frames, dtype=bool)
        is_speech = False
        hangover_counter = 0

        for i in range(num_frames):
            e = frame_energies_db[i]
            if not is_speech:
                if e >= high_threshold:
                    is_speech = True
                    speech_mask[i] = True
            else:
                if e >= low_threshold:
                    speech_mask[i] = True
                    hangover_counter = cls.HANGOVER_FRAMES
                elif hangover_counter > 0:
                    speech_mask[i] = True
                    hangover_counter -= 1
                else:
                    is_speech = False

        speech_frame_count = int(np.sum(speech_mask))
        if speech_frame_count == 0:
            # Entirely silent
            return VADTrimmingResult(
                original_duration_ms=total_duration_ms,
                trimmed_duration_ms=total_duration_ms,
                head_silence_ms=total_duration_ms,
                tail_silence_ms=0,
                voice_activity_ratio=0.0,
                optimal_threshold_db=round(best_threshold_db, 1),
                start_sample=0,
                end_sample=total_samples,
            )

        # 4. Find speech boundaries
        speech_indices = np.where(speech_mask)[0]
        first_frame = int(speech_indices[0])
        last_frame = int(speech_indices[-1])

        first_sample = max(0, first_frame * hop_len - int(sample_rate * (cls.PAD_HEAD_MS / 1000.0)))
        last_sample = min(total_samples, (last_frame * hop_len + frame_len) + int(sample_rate * (cls.PAD_TAIL_MS / 1000.0)))

        head_silence_ms = int((first_sample / sample_rate) * 1000)
        tail_silence_ms = int(((total_samples - last_sample) / sample_rate) * 1000)
        trimmed_duration_ms = max(50, int(((last_sample - first_sample) / sample_rate) * 1000))
        var = round(min(1.0, float(speech_frame_count) / max(1.0, float(num_frames))), 3)

        return VADTrimmingResult(
            original_duration_ms=total_duration_ms,
            trimmed_duration_ms=trimmed_duration_ms,
            head_silence_ms=head_silence_ms,
            tail_silence_ms=tail_silence_ms,
            voice_activity_ratio=var,
            optimal_threshold_db=round(best_threshold_db, 1),
            start_sample=first_sample,
            end_sample=last_sample,
        )
