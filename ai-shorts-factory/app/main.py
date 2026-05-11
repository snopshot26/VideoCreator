from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.logger import setup_logging
from pipeline.orchestrator import run_batch


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="AI Shorts Factory CLI")
    parser.add_argument("--batch", type=Path, help="Path to batch_prompts.txt (one idea per line)")
    args = parser.parse_args()

    if args.batch:
        lines = Path(args.batch).read_text(encoding="utf-8").splitlines()
        out = run_batch(lines)
        print(f"Batch complete: {out}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
