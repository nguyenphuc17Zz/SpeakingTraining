import asyncio
import gc
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.domains.speech.errors import STTUnavailableError

settings = get_settings()

# Automatically register NVIDIA CUDA 12 and cuDNN library directories on Windows
if sys.platform == "win32":
    try:
        venv_base = Path(sys.prefix)
        for nvidia_bin in venv_base.glob("Lib/site-packages/nvidia/*/bin"):
            if nvidia_bin.exists():
                os.add_dll_directory(str(nvidia_bin))
                os.environ["PATH"] = str(nvidia_bin) + os.pathsep + os.environ.get("PATH", "")
        ct2_dir = venv_base / "Lib" / "site-packages" / "ctranslate2"
        if ct2_dir.exists():
            os.add_dll_directory(str(ct2_dir))
    except Exception as _dll_e:
        logger.debug(f"[WhisperModelManager] Windows DLL registration notice: {_dll_e}")


class WhisperModelManager:
    """
    GPU/CPU Resource-aware Manager for Faster-Whisper models.
    Provides LRU model eviction, memory protection, hardware auto-detection,
    and thread-safe model lifecycle management.
    """

    def __init__(self, max_loaded_models: int | None = None):
        self.max_loaded_models = max_loaded_models or getattr(settings, "WHISPER_MAX_LOADED_MODELS", 2)
        self._models: OrderedDict[tuple[str, str, str], dict[str, Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._active_model_id: str = "small"

    def set_active_model(self, model_id: str) -> str:
        self._active_model_id = model_id.lower().strip()
        logger.info(f"[WhisperModelManager] Set system-wide active Whisper model to: '{self._active_model_id}'")
        return self._active_model_id

    def get_active_model_id(self) -> str:
        return self._active_model_id

    @classmethod
    def detect_hardware(cls, preferred_device: str = "auto", preferred_compute: str = "auto") -> tuple[str, str]:
        """Detects whether CUDA is available and selects optimal compute type (prioritizing GPU)."""
        device = (preferred_device or "auto").lower().strip()
        compute = (preferred_compute or "auto").lower().strip()

        if device in ("auto", "cuda"):
            try:
                import ctranslate2
                cuda_avail = ctranslate2.get_cuda_device_count() > 0
                if cuda_avail:
                    device = "cuda"
                    compute = "float16" if compute == "auto" else compute
                    logger.info("[WhisperModelManager] GPU Hardware Active: NVIDIA RTX GPU detected (CUDA float16 enabled).")
                else:
                    if preferred_device == "cuda":
                        logger.warning("[WhisperModelManager] CUDA requested but no NVIDIA GPU detected. Falling back to CPU.")
                    device = "cpu"
                    compute = "int8" if compute == "auto" else compute
            except Exception as e:
                logger.warning(f"[WhisperModelManager] Failed to detect CUDA hardware: {e}. Falling back to CPU.")
                device = "cpu"
                compute = "int8" if compute == "auto" else compute

        elif device == "cpu":
            compute = "int8" if compute == "auto" else compute

        return device, compute

    def _evict_oldest_model_sync(self) -> str | None:
        """Evicts the least recently used model from memory."""
        if not self._models:
            return None

        key, entry = self._models.popitem(last=False)
        evicted_name = f"{key[0]} (device={key[1]}, compute={key[2]})"
        logger.info(f"[WhisperModelManager] Evicting LRU model '{evicted_name}' to free memory...")

        # Explicitly delete model and garbage collect
        del entry["model"]
        gc.collect()

        try:
            import ctranslate2
            # Clear CUDA caches if supported
            if hasattr(ctranslate2, "empty_cache"):
                ctranslate2.empty_cache()
        except Exception:
            pass

        return evicted_name

    def get_or_load_model(self, model_size: str, device: str = "auto", compute_type: str = "auto") -> Any:
        """
        Synchronous model loader designed to be called inside worker thread pool (e.g. via asyncio.to_thread).
        """
        resolved_device, resolved_compute = self.detect_hardware(device, compute_type)
        key = (model_size.lower().strip(), resolved_device, resolved_compute)

        # Cache Hit
        if key in self._models:
            entry = self._models[key]
            entry["last_used_at"] = time.time()
            entry["use_count"] = entry.get("use_count", 0) + 1
            self._models.move_to_end(key)
            return entry["model"]

        # Evict oldest if exceeding capacity
        while len(self._models) >= self.max_loaded_models:
            self._evict_oldest_model_sync()

        # Load new model
        try:
            from faster_whisper import WhisperModel

            logger.info(
                f"[WhisperModelManager] Loading Faster-Whisper model '{model_size}' on device={resolved_device}, compute_type={resolved_compute}..."
            )
            start_load = time.perf_counter()
            model = WhisperModel(
                model_size_or_path=model_size,
                device=resolved_device,
                compute_type=resolved_compute,
            )
            load_ms = (time.perf_counter() - start_load) * 1000
            logger.info(
                f"[WhisperModelManager] Model '{model_size}' loaded in {load_ms:.1f}ms. Total resident models: {len(self._models) + 1}/{self.max_loaded_models}"
            )

            self._models[key] = {
                "model": model,
                "model_size": model_size,
                "device": resolved_device,
                "compute_type": resolved_compute,
                "loaded_at": time.time(),
                "last_used_at": time.time(),
                "use_count": 1,
                "load_duration_ms": load_ms,
            }
            return model

        except Exception as e:
            logger.error(f"[WhisperModelManager] Failed to load model '{model_size}': {e}", exc_info=True)
            raise STTUnavailableError(
                message=f"Failed to load Faster-Whisper model '{model_size}': {str(e)}",
                provider_id="faster_whisper",
                raw_error=e,
            )

    @classmethod
    def get_cache_dir(cls) -> "Path":
        from pathlib import Path
        import os
        return Path(os.path.expanduser("~/.cache/huggingface/hub"))

    @classmethod
    def is_model_downloaded(cls, model_id: str) -> bool:
        from pathlib import Path
        import os
        cache_dir = Path(os.path.expanduser("~/.cache/huggingface/hub"))
        if not cache_dir.exists():
            return False
        
        m_id = model_id.lower().strip()
        patterns = [
            f"models--Systran--faster-whisper-{m_id}",
            f"models--deepdml--faster-whisper-{m_id}-ct2",
        ]
        if m_id == "turbo":
            patterns.extend([
                "models--Systran--faster-whisper-large-v3-turbo",
                "models--deepdml--faster-whisper-large-v3-turbo-ct2",
                "models--Systran--faster-whisper-turbo",
            ])
            
        for pattern in patterns:
            target = cache_dir / pattern
            if target.exists():
                snapshots = target / "snapshots"
                if snapshots.exists() and any(snapshots.iterdir()):
                    return True
        return False

    def get_available_models_info(self, active_model: str = "base") -> list[dict[str, Any]]:
        """Returns comprehensive catalog of all Whisper models with download and hardware status."""
        device, compute = self.detect_hardware()
        is_gpu = device == "cuda"
        
        models_catalog = [
            {
                "id": "tiny",
                "name": "Whisper Tiny",
                "params": "39M",
                "size_mb": 75,
                "size_display": "~75 MB",
                "ram_required": "~500 MB RAM",
                "stars": 2,
                "speed_rating": "Cực nhanh (<100ms)",
                "accuracy_rating": "Cơ bản (N5)",
                "recommended_for": "Máy yếu / CPU thấp / Bắt từ khóa nhanh",
                "description_vi": "Model siêu nhẹ, tải nhanh trong vài giây. Thích hợp cho máy tính không có GPU hoặc chỉ cần nhận diện từ khóa ngắn.",
                "is_recommended": not is_gpu,
            },
            {
                "id": "base",
                "name": "Whisper Base",
                "params": "74M",
                "size_mb": 145,
                "size_display": "~145 MB",
                "ram_required": "~1 GB RAM",
                "stars": 3,
                "speed_rating": "Rất nhanh (~150ms)",
                "accuracy_rating": "Khá (N5 - N3)",
                "recommended_for": "Tiêu chuẩn cân bằng / Phổ biến nhất",
                "description_vi": "Model chuẩn của hệ thống. Tốc độ nhận diện nhanh, chính xác với các câu hội thoại tiếng Nhật sơ cấp và trung cấp.",
                "is_recommended": not is_gpu,
            },
            {
                "id": "small",
                "name": "Whisper Small",
                "params": "244M",
                "size_mb": 460,
                "size_display": "~460 MB",
                "ram_required": "~2 GB RAM/VRAM",
                "stars": 4,
                "speed_rating": "Nhanh (~250ms)",
                "accuracy_rating": "Tốt (Phát âm chi tiết)",
                "recommended_for": "Luyện phát âm chuẩn / Bắt rõ trợ từ",
                "description_vi": "Phân tích âm vị (mora) và trợ từ (は/が/を/に) rõ ràng hơn. Rất khuyến nghị cho người học muốn chấm phát âm chuẩn xác.",
                "is_recommended": False,
            },
            {
                "id": "medium",
                "name": "Whisper Medium",
                "params": "769M",
                "size_mb": 1500,
                "size_display": "~1.5 GB",
                "ram_required": "~4 GB (Khuyên dùng GPU)",
                "stars": 5,
                "speed_rating": "Chuẩn (~400ms)",
                "accuracy_rating": "Rất cao (Hội thoại tự nhiên)",
                "recommended_for": "Hội thoại N2-N1 / Ngữ cảnh phức tạp",
                "description_vi": "Độ chính xác rất cao cho tiếng Nhật giao tiếp thực tế, hiểu rõ kính ngữ Keigo, từ lóng và ngữ cảnh dài.",
                "is_recommended": is_gpu,
            },
            {
                "id": "turbo",
                "name": "Whisper Large-v3 Turbo",
                "params": "809M",
                "size_mb": 1600,
                "size_display": "~1.6 GB",
                "ram_required": "~4.5 GB VRAM",
                "stars": 5,
                "speed_rating": "Tốc độ cao 8x (Khuyên dùng GPU)",
                "accuracy_rating": "Xuất sắc (Tối ưu nhất)",
                "recommended_for": "Trải nghiệm hoàn hảo nhất trên GPU",
                "description_vi": "Phiên bản Turbo thế hệ mới của OpenAI: Chính xác tương đương Large-v3 nhưng tốc độ xử lý nhanh gấp 4-8 lần. Lựa chọn số 1 nếu có card NVIDIA.",
                "is_recommended": is_gpu,
            },
            {
                "id": "large-v3",
                "name": "Whisper Large-v3",
                "params": "1550M",
                "size_mb": 3100,
                "size_display": "~3.1 GB",
                "ram_required": "~6 - 8 GB VRAM",
                "stars": 5,
                "speed_rating": "Chuẩn (~600ms)",
                "accuracy_rating": "Đỉnh cao (SOTA)",
                "recommended_for": "Độ chính xác tối đa / Song ngữ Nhật-Anh",
                "description_vi": "Model lớn nhất với độ chính xác số 1 thế giới. Nhận diện hoàn hảo mọi sắc thái phát âm, ngữ điệu và câu đàm thoại phức tạp.",
                "is_recommended": False,
            },
        ]

        active_id = active_model.lower().strip()
        loaded_keys = {k[0] for k in self._models.keys()}

        for m in models_catalog:
            m_id = m["id"]
            m["is_downloaded"] = self.is_model_downloaded(m_id)
            m["is_loaded"] = m_id in loaded_keys
            m["is_active"] = m_id == active_id
            m["device"] = device
            m["compute_type"] = compute

        return models_catalog

    def download_model_sync(self, model_size: str) -> str:
        """Downloads model synchronously via faster_whisper download_model."""
        from faster_whisper import download_model
        resolved_name = model_size.lower().strip()
        if resolved_name == "turbo":
            resolved_name = "deepdml/faster-whisper-large-v3-turbo-ct2"
        logger.info(f"[WhisperModelManager] Downloading Faster-Whisper model '{model_size}' ({resolved_name})...")
        path = download_model(resolved_name)
        logger.info(f"[WhisperModelManager] Downloaded model '{model_size}' to {path}")
        return str(path)

    def evict_all(self) -> int:
        """Evicts all resident models from memory."""
        count = len(self._models)
        self._models.clear()
        gc.collect()
        logger.info(f"[WhisperModelManager] Evicted all {count} models from memory.")
        return count

    def get_status(self) -> dict[str, Any]:
        """Returns diagnostic telemetry on loaded models and GPU hardware."""
        cuda_count = 0
        try:
            import ctranslate2
            cuda_count = ctranslate2.get_cuda_device_count()
        except Exception:
            pass

        loaded_info = []
        for key, entry in self._models.items():
            loaded_info.append({
                "model_size": entry["model_size"],
                "device": entry["device"],
                "compute_type": entry["compute_type"],
                "loaded_at": entry["loaded_at"],
                "last_used_at": entry["last_used_at"],
                "use_count": entry["use_count"],
                "load_duration_ms": round(entry["load_duration_ms"], 1),
            })

        return {
            "cuda_available": cuda_count > 0,
            "cuda_device_count": cuda_count,
            "max_loaded_models": self.max_loaded_models,
            "loaded_models_count": len(self._models),
            "loaded_models": loaded_info,
        }


# Global singleton instance
whisper_model_manager = WhisperModelManager()

