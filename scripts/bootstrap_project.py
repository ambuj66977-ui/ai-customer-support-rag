"""Rebuild every generated artifact needed to run the project locally."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATASET = PROJECT_ROOT / "data" / "raw" / "customer_support_synthetic.csv"
STEPS = (
    ("Validating the raw dataset", [sys.executable, "scripts/validate_raw_dataset.py"]),
    ("Preprocessing FAQ documents", [sys.executable, "-m", "src.preprocessing"]),
    ("Building the FAISS index", [sys.executable, "build_index.py"]),
)


def main() -> None:
    """Run the deterministic local build in dependency order."""
    if RAW_DATASET.exists():
        print("→ Raw dataset already exists; preserving it", flush=True)
    else:
        print("→ Generating the synthetic FAQ dataset", flush=True)
        subprocess.run(
            [sys.executable, "scripts/generate_synthetic_dataset.py"],
            cwd=PROJECT_ROOT,
            check=True,
        )
    for label, command in STEPS:
        print(f"\n→ {label}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    print("\n✓ Local RAG artifacts are ready. Run: streamlit run app.py", flush=True)


if __name__ == "__main__":
    main()
