import logging
import re
import sys

# Pattern for masking potential API keys or sensitive values in log messages
SECRET_PATTERNS = [
    re.compile(r"(AIzaSy[a-zA-Z0-9_\-]{33})"),            # Gemini API Key
    re.compile(r"(gsk_[a-zA-Z0-9]{32,})"),                 # Groq API Key
    re.compile(r"(sk-or-v1-[a-zA-Z0-9]{64})"),             # OpenRouter API Key
    re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"),               # General OpenAI/other API keys
    re.compile(r"(password=['\"]?)([^'\"]+)(['\"]?)", re.IGNORECASE),
]


class SecretMaskingFilter(logging.Filter):
    """Logging filter that scrubs plaintext API keys and secrets from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.mask_secrets(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_secrets(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @staticmethod
    def mask_secrets(text: str) -> str:
        for pattern in SECRET_PATTERNS:
            text = pattern.sub(r"[REDACTED_SECRET]", text)
        return text


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures structured, secret-safe application logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("speaking_training")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretMaskingFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
