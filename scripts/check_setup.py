from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings, missing_required_settings
import database


def main():
    missing = missing_required_settings()
    if missing:
        print("Missing:", ", ".join(missing))
        raise SystemExit(1)
    settings = get_settings()
    print("Groq model:", settings.groq_model)
    print("Supabase URL configured: yes")
    database.health_check()
    print("Supabase schema connection: OK")
    print("Setup looks ready.")


if __name__ == "__main__":
    main()
