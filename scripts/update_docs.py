#!/usr/bin/env python3
"""Sync the year-dependent prose in README.md and docs/index.html.

The years come from the riders history CSVs, so this needs no arguments in
the normal case:

    uv run python scripts/update_docs.py              # rewrite the files
    uv run python scripts/update_docs.py --check       # fail if out of date
"""

from pathlib import Path

import fire

from letourdataset.coverage import load_coverage
from letourdataset.docsync import sync_all

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(check: bool = False, data_root: str | None = None) -> None:
    """Rewrite the generated coverage blocks from the CSV data.

    Args:
        check: Report what would change and exit non-zero instead of writing.
            Used by CI to catch a README that drifted from the data.
        data_root: Data directory to read; defaults to `<repo>/data`.

    Raises:
        SystemExit: With code 1 when `check` finds a file out of date.
    """
    root = Path(data_root) if data_root else REPO_ROOT / "data"
    coverage = load_coverage(root)

    for race in coverage.values():
        print(
            f"📊 {race.name}: {race.first_year} - {race.latest_year} "
            f"({race.editions} editions)"
        )

    changed = sync_all(REPO_ROOT, coverage, write=not check)
    stale = [name for name, was_changed in changed.items() if was_changed]

    if not stale:
        print("✅ README.md and docs/index.html already match the data")
        return

    if check:
        print(f"❌ Out of date with the data: {', '.join(stale)}")
        print("   Run 'make docs' to update them.")
        raise SystemExit(1)

    for name in stale:
        print(f"✅ Updated {name}")


if __name__ == "__main__":
    fire.Fire(main)
