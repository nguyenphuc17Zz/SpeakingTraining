from typing import Any
import numpy as np


class VADAnalyzer:
    """Performs energy-based Voice Activity Detection on 16kHz mono audio."""

    FRAME_MS = 20           # 20ms frame
    FRAME_SAMPLES = 320     # 16000 * 0.02
    ENERGY_THRESHOLD = 0.008  # RMS energy threshold for voiced frames

    @classmethod
    def analyze(cls, samples: np.ndarray, sample_rate: int = 16000) -> dict[str, Any]:
        """
        Extracts speech segments, silence ratio, speech start/end timestamps.
        Returns:
            - speech_start_ms: int
            - speech_end_ms: int
            - total_speech_ms: int
            - silence_ratio: float
            - speech_segments: list[tuple[int, int]]  # [(start_ms, end_ms), ...]
            - pauses: list[tuple[int, int, int]]      # [(start_ms, end_ms, duration_ms), ...]
        """
        if len(samples) == 0:
            return {
                "speech_start_ms": 0,
                "speech_end_ms": 0,
                "total_speech_ms": 0,
                "silence_ratio": 1.0,
                "speech_segments": [],
                "pauses": [],
            }

        total_frames = len(samples) // cls.FRAME_SAMPLES
        frame_energies = []
        is_speech_frame = []

        for f in range(total_frames):
            frame = samples[f * cls.FRAME_SAMPLES : (f + 1) * cls.FRAME_SAMPLES]
            rms = float(np.sqrt(np.mean(frame**2)))
            frame_energies.append(rms)
            is_speech_frame.append(rms > cls.ENERGY_THRESHOLD)

        # Smooth speech activity with a small 3-frame window
        smoothed = []
        for i in range(len(is_speech_frame)):
            window = is_speech_frame[max(0, i - 1) : min(len(is_speech_frame), i + 2)]
            smoothed.append(sum(window) >= 2)

        # Group contiguous speech and silence regions
        speech_segments: list[tuple[int, int]] = []
        pauses: list[tuple[int, int, int]] = []

        in_speech = False
        seg_start = 0

        for i, val in enumerate(smoothed):
            time_ms = i * cls.FRAME_MS
            if val and not in_speech:
                in_speech = True
                seg_start = time_ms
            elif not val and in_speech:
                in_speech = False
                speech_segments.append((seg_start, time_ms))

        if in_speech:
            speech_segments.append((seg_start, total_frames * cls.FRAME_MS))

        # Detect pauses inside the speech envelope
        if speech_segments:
            speech_start_ms = speech_segments[0][0]
            speech_end_ms = speech_segments[-1][1]

            for i in range(len(speech_segments) - 1):
                pause_start = speech_segments[i][1]
                pause_end = speech_segments[i + 1][0]
                pause_dur = pause_end - pause_start
                if pause_dur >= 100:  # Pauses >= 100ms
                    pauses.append((pause_start, pause_end, pause_dur))

            total_speech_ms = sum([end - start for start, end in speech_segments])
            total_duration_ms = total_frames * cls.FRAME_MS
            silence_ratio = 1.0 - (total_speech_ms / float(max(1, total_duration_ms)))
        else:
            speech_start_ms = 0
            speech_end_ms = 0
            total_speech_ms = 0
            silence_ratio = 1.0

        return {
            "speech_start_ms": speech_start_ms,
            "speech_end_ms": speech_end_ms,
            "total_speech_ms": total_speech_ms,
            "silence_ratio": round(silence_ratio, 3),
            "speech_segments": speech_segments,
            "pauses": pauses,
        }
