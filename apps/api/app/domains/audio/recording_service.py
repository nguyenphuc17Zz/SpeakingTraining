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
        )
