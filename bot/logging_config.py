"""Logging ka central setup.

Do jagah log jaata hai:
  * ek rotating log file logs/ ke andar (poora detail, ye hi deliverable hai)
  * console pe (sirf info aur upar, taaki CLI clean dikhe)

Sensitive cheezein (API key, signature) kabhi log nahi hoti - client redact
karke hi logger ko bhejta hai.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_CONSOLE_FORMAT = "%(levelname)-8s | %(message)s"

_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Root logging ko ek baar setup karo aur bot logger return karo.

    Baar baar call karna safe hai - handler sirf pehli baar attach hote hain.
    """
    global _configured

    logger = logging.getLogger("trading_bot")

    # Pehle se setup hai to dobara kuch mat karo
    if _configured:
        return logger

    os.makedirs(LOG_DIR, exist_ok=True)
    logger.setLevel(logging.DEBUG)

    # File handler - sab kuch, rotate hota hai taaki log infinite na badhe
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    # Console handler - readable, info aur upar. stdout use kar rahe taaki log
    # lines CLI ke print() summary ke saath sahi order me dikhe.
    # Windows ka default console encoding (cp1252) kuch chars pe crash kar deta
    # hai, isliye stdout ko utf-8 + replace pe reconfigure karte hain (guarded).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    _configured = True
    logger.debug("Logging ready. Log file: %s", LOG_FILE)
    return logger


def get_logger() -> logging.Logger:
    """Bot logger return karo, zarurat ho to default se setup kar deta hai."""
    return setup_logging()
