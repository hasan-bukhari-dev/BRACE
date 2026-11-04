"""One application version shared by source, desktop and evidence exports."""
from pathlib import Path

VERSION = (Path(__file__).resolve().parents[1] / 'VERSION').read_text(encoding='utf-8').strip()
