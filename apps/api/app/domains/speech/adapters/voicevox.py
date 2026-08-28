import time
from typing import Any

import httpx

from app.core.logging import logger
from app.domains.speech.contracts import (
    TTSAudioOutput,
    TTSOptions,
    TTSProvider,
    TTSVoice,
)
from app.domains.speech.errors import TTSProviderError, TTSUnavailableError


class VoicevoxAdapter(TTSProvider):
    """Production VOICEVOX Text-to-Speech adapter via HTTP Engine API."""

    provider_id: str = "voicevox"

    # Default fallback voices catalog (full official VOICEVOX character & style catalog)
    FALLBACK_VOICES = [
        # Shikoku Metan
        TTSVoice(id="1", name="四国めたん (Shikoku Metan - Normal)", speaker_id=2, gender="female", style="Normal"),
        TTSVoice(id="2", name="四国めたん (Shikoku Metan - あまあま)", speaker_id=0, gender="female", style="あまあま"),
        TTSVoice(id="3", name="四国めたん (Shikoku Metan - ツンツン)", speaker_id=6, gender="female", style="ツンツン"),
        TTSVoice(id="4", name="四国めたん (Shikoku Metan - セクシー)", speaker_id=4, gender="female", style="セクシー"),
        # Zundamon
        TTSVoice(id="5", name="ずんだもん (Zundamon - Normal)", speaker_id=3, gender="female", style="Normal"),
        TTSVoice(id="6", name="ずんだもん (Zundamon - あまあま)", speaker_id=1, gender="female", style="あまあま"),
        TTSVoice(id="7", name="ずんだもん (Zundamon - ツンツン)", speaker_id=7, gender="female", style="ツンツン"),
        TTSVoice(id="8", name="ずんだもん (Zundamon - セクシー)", speaker_id=5, gender="female", style="セクシー"),
        TTSVoice(id="9", name="ずんだもん (Zundamon - ささやき)", speaker_id=22, gender="female", style="ささやき"),
        # Kasukabe Tsumugi
        TTSVoice(id="10", name="春日部つむぎ (Kasukabe Tsumugi - Normal)", speaker_id=8, gender="female", style="Normal"),
        # Amehare Hau
        TTSVoice(id="11", name="雨晴はう (Amehare Hau - Normal)", speaker_id=10, gender="female", style="Normal"),
        # Namino Ritsu
        TTSVoice(id="12", name="波音リツ (Namino Ritsu - Normal)", speaker_id=9, gender="female", style="Normal"),
        TTSVoice(id="13", name="波音リツ (Namino Ritsu - クイーン)", speaker_id=65, gender="female", style="クイーン"),
        # Kurono Takehiro
        TTSVoice(id="14", name="玄野武宏 (Kurono Takehiro - Normal)", speaker_id=11, gender="male", style="Normal"),
        TTSVoice(id="15", name="玄野武宏 (Kurono Takehiro - 喜び)", speaker_id=39, gender="male", style="喜び"),
        TTSVoice(id="16", name="玄野武宏 (Kurono Takehiro - ツンツン)", speaker_id=40, gender="male", style="ツンツン"),
        # Shirakami Kotaro
        TTSVoice(id="17", name="白上虎太郎 (Shirakami Kotaro - ふつう)", speaker_id=12, gender="male", style="ふつう"),
        TTSVoice(id="18", name="白上虎太郎 (Shirakami Kotaro - わーい)", speaker_id=32, gender="male", style="わーい"),
        # Aoyama Ryusei
        TTSVoice(id="19", name="青山龍星 (Aoyama Ryusei - Normal)", speaker_id=13, gender="male", style="Normal"),
        TTSVoice(id="20", name="青山龍星 (Aoyama Ryusei - 熱血)", speaker_id=81, gender="male", style="熱血"),
        # Meimei Himari
        TTSVoice(id="21", name="冥鳴ひまり (Meimei Himari - Normal)", speaker_id=14, gender="female", style="Normal"),
        # Kyushu Sora
        TTSVoice(id="22", name="九州そら (Kyushu Sora - Normal)", speaker_id=16, gender="female", style="Normal"),
        TTSVoice(id="23", name="九州そら (Kyushu Sora - あまあま)", speaker_id=15, gender="female", style="あまあま"),
        TTSVoice(id="24", name="九州そら (Kyushu Sora - ツンツン)", speaker_id=18, gender="female", style="ツンツン"),
        # Mochiko-san
        TTSVoice(id="25", name="もち子さん (Mochiko-san - Normal)", speaker_id=20, gender="female", style="Normal"),
        # Kenzaki Mesuo
        TTSVoice(id="26", name="剣崎雌雄 (Kenzaki Mesuo - Normal)", speaker_id=21, gender="male", style="Normal"),
        # WhiteCUL
        TTSVoice(id="27", name="WhiteCUL (WhiteCUL - Normal)", speaker_id=23, gender="female", style="Normal"),
        TTSVoice(id="28", name="WhiteCUL (WhiteCUL - たのしい)", speaker_id=24, gender="female", style="たのしい"),
        TTSVoice(id="29", name="WhiteCUL (WhiteCUL - かなしい)", speaker_id=25, gender="female", style="かなしい"),
        # Goki
        TTSVoice(id="30", name="後鬼 (Goki - 人間ver.)", speaker_id=27, gender="female", style="人間ver."),
        TTSVoice(id="31", name="後鬼 (Goki - 鬼ver.)", speaker_id=28, gender="female", style="鬼ver."),
        # No.7
        TTSVoice(id="32", name="No.7 (Seven - Normal)", speaker_id=29, gender="female", style="Normal"),
        TTSVoice(id="33", name="No.7 (Seven - アナウンス)", speaker_id=30, gender="female", style="アナウンス"),
        # Chibi Shikijii
        TTSVoice(id="34", name="ちび式じい (Chibi Shikijii - Normal)", speaker_id=42, gender="male", style="Normal"),
        # Sayo
        TTSVoice(id="35", name="小夜/SORYU (Sayo - Normal)", speaker_id=46, gender="female", style="Normal"),
        # Nurse Robot Type T
        TTSVoice(id="36", name="ナースロボ＿タイプＴ (Nurse Robot Type T - Normal)", speaker_id=47, gender="female", style="Normal"),
        TTSVoice(id="37", name="ナースロボ＿タイプＴ (Nurse Robot Type T - 楽々)", speaker_id=48, gender="female", style="楽々"),
        # Tohoku Trio: Zunko, Kiritan, Itako
        TTSVoice(id="38", name="東北ずん子 (Tohoku Zunko - Normal)", speaker_id=56, gender="female", style="Normal"),
        TTSVoice(id="39", name="東北きりたん (Tohoku Kiritan - Normal)", speaker_id=57, gender="female", style="Normal"),
        TTSVoice(id="40", name="東北イタコ (Tohoku Itako - Normal)", speaker_id=58, gender="female", style="Normal"),
        # Chugoku Usagi
        TTSVoice(id="41", name="中国うさぎ (Chugoku Usagi - Normal)", speaker_id=61, gender="female", style="Normal"),
        TTSVoice(id="42", name="中国うさぎ (Chugoku Usagi - おどろき)", speaker_id=62, gender="female", style="おどろき"),
        # Kurita Maron
        TTSVoice(id="43", name="栗田まろん (Kurita Maron - Normal)", speaker_id=67, gender="male", style="Normal"),
        # Aiel Tan
        TTSVoice(id="44", name="あいえるたん (Aiel Tan - Normal)", speaker_id=68, gender="female", style="Normal"),
        # Manbetsu Hanamaru
        TTSVoice(id="45", name="満別花丸 (Manbetsu Hanamaru - Normal)", speaker_id=69, gender="female", style="Normal"),
        # Kotoyomi Nia
        TTSVoice(id="46", name="琴詠ニア (Kotoyomi Nia - Normal)", speaker_id=70, gender="female", style="Normal"),
    ]

    def __init__(
        self,
        engine_url: str = "http://127.0.0.1:50021",
        timeout_seconds: float = 30.0,
    ):
        self.engine_url = engine_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=5.0),
            follow_redirects=True,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check if VOICEVOX engine is reachable and returning speakers."""
        url = f"{self.engine_url}/version"
        start_time = time.perf_counter()
        try:
            async with self._get_client() as client:
                resp = await client.get(url)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                if resp.status_code == 200:
                    version = resp.text.strip().replace('"', '')
                    voices = await self.get_available_voices()
                    return {
                        "is_available": True,
                        "status_message": f"VOICEVOX engine online (v{version})",
                        "latency_ms": latency_ms,
                        "available_voices_count": len(voices),
                    }
                return {
                    "is_available": False,
                    "status_message": f"VOICEVOX returned status {resp.status_code}",
                    "latency_ms": latency_ms,
                    "available_voices_count": len(self.FALLBACK_VOICES),
                }
        except Exception as e:
            return {
                "is_available": False,
                "status_message": f"VOICEVOX engine offline ({str(e)})",
                "latency_ms": None,
                "available_voices_count": len(self.FALLBACK_VOICES),
            }

    async def get_available_voices(self) -> list[TTSVoice]:
        """Fetch available speakers from VOICEVOX engine."""
        url = f"{self.engine_url}/speakers"
        try:
            async with self._get_client() as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.warning(
                        f"[VOICEVOX] /speakers returned {response.status_code}, using fallback voice catalog."
                    )
                    return self.FALLBACK_VOICES

                MALE_NAMES = {
                    "玄野武宏", "白上虎太郎", "青山龍星", "剣崎雌雄", "ちび式じい",
                    "†聖騎士 紅桜†", "雀松朱司", "麒ヶ島宗麟", "栗田まろん", "ナマハゲ直伝"
                }
                speakers_data = response.json()
                voices: list[TTSVoice] = []
                for spk in speakers_data:
                    name = spk.get("name", "Unknown")
                    is_male = any(m in name for m in MALE_NAMES) or "男" in str(spk)
                    gender = "male" if is_male else "female"
                    for style in spk.get("styles", []):
                        style_id = style.get("id")
                        style_name = style.get("name", "Normal")
                        voices.append(
                            TTSVoice(
                                id=str(style_id),
                                name=f"{name} ({style_name})",
                                speaker_id=style_id,
                                gender=gender,
                                style=style_name,
                                capabilities=["speed_control", "pitch_control", "volume_control"],
                            )
                        )
                return voices if voices else self.FALLBACK_VOICES
        except Exception as e:
            logger.warning(f"[VOICEVOX] Engine offline or unreachable at {url}: {e}. Using fallback voice list.")
            return self.FALLBACK_VOICES

    async def synthesize(
        self,
        text: str,
        options: TTSOptions | None = None,
    ) -> TTSAudioOutput:
        """Synthesize Japanese speech text to WAV audio using VOICEVOX engine."""
        if not text or not text.strip():
            return TTSAudioOutput(
                audio_bytes=b"",
                format="wav",
                duration_ms=0,
                sample_rate=24000,
                voice="default",
                provider=self.provider_id,
                processing_time_ms=0,
            )

        opts = options or TTSOptions()
        speaker_id = opts.speaker_id
        try:
            if opts.voice_id and opts.voice_id.isdigit():
                speaker_id = int(opts.voice_id)
        except Exception:
            speaker_id = 1

        start_time = time.perf_counter()

        try:
            async with self._get_client() as client:
                # 1. Generate audio query
                query_url = f"{self.engine_url}/audio_query"
                query_resp = await client.post(
                    query_url,
                    params={"text": text, "speaker": speaker_id},
                )
                if query_resp.status_code != 200:
                    raise TTSProviderError(
                        message=f"VOICEVOX audio_query failed with HTTP {query_resp.status_code}: {query_resp.text}",
                        provider_id=self.provider_id,
                        raw_error=query_resp.text,
                    )

                audio_query = query_resp.json()

                # Adjust parameters if specified
                if opts.speed != 1.0:
                    audio_query["speedScale"] = opts.speed
                if opts.pitch != 0.0:
                    audio_query["pitchScale"] = opts.pitch
                if opts.volume != 1.0:
                    audio_query["volumeScale"] = opts.volume

                # 2. Synthesize audio
                synth_url = f"{self.engine_url}/synthesis"
                synth_resp = await client.post(
                    synth_url,
                    params={"speaker": speaker_id},
                    json=audio_query,
                    headers={"Content-Type": "application/json"},
                )
                if synth_resp.status_code != 200:
                    raise TTSProviderError(
                        message=f"VOICEVOX synthesis failed with HTTP {synth_resp.status_code}: {synth_resp.text}",
                        provider_id=self.provider_id,
                        raw_error=synth_resp.text,
                    )

                audio_bytes = synth_resp.content
                proc_ms = int((time.perf_counter() - start_time) * 1000)

                # Estimate duration from WAV bytes size (24kHz 16-bit mono = ~48000 bytes/sec)
                duration_ms = None
                if len(audio_bytes) > 44:
                    raw_audio_len = len(audio_bytes) - 44
                    duration_ms = int((raw_audio_len / 48000.0) * 1000)

                logger.info(
                    f"[VOICEVOX] Synthesized {len(text)} chars -> {len(audio_bytes)} bytes WAV in {proc_ms}ms"
                )

                return TTSAudioOutput(
                    audio_bytes=audio_bytes,
                    format="wav",
                    duration_ms=duration_ms,
                    sample_rate=24000,
                    voice=str(speaker_id),
                    provider=self.provider_id,
                    processing_time_ms=proc_ms,
                    metadata={"speaker_id": speaker_id, "speed": opts.speed, "pitch": opts.pitch},
                )

        except httpx.ConnectError as ce:
            logger.warning(f"[VOICEVOX] Cannot connect to VOICEVOX engine at {self.engine_url}: {ce}")
            raise TTSUnavailableError(
                message=f"VOICEVOX engine offline at {self.engine_url}. Start VOICEVOX app to enable speech playback.",
                provider_id=self.provider_id,
                raw_error=ce,
            )
        except (TTSProviderError, TTSUnavailableError):
            raise
        except Exception as e:
            logger.error(f"[VOICEVOX] Unexpected synthesis error: {e}", exc_info=True)
            raise TTSProviderError(
                message=f"VOICEVOX synthesis error: {str(e)}",
                provider_id=self.provider_id,
                raw_error=e,
            )
