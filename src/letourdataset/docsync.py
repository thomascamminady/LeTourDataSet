#!/usr/bin/env python3
"""Rewrite the year-dependent prose in README.md and docs/index.html.

Both files carry `<!-- coverage:start -->` / `<!-- coverage:end -->` markers
around the few lines that name a year. The text between them is generated
from `coverage.load_coverage()`, so an annual update never has to touch it.
"""

import re
from collections.abc import Callable
from pathlib import Path

from letourdataset.coverage import MEN, WOMEN, RaceCoverage

MARKER = "coverage"

Renderer = Callable[[dict[str, RaceCoverage]], str]


def _block_pattern(marker: str) -> re.Pattern[str]:
    start, end = f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"
    return re.compile(
        rf"({re.escape(start)}\n)(.*?)(\n{re.escape(end)})",
        re.DOTALL,
    )


def replace_block(text: str, body: str, marker: str = MARKER) -> str:
    """Replace the text between the marker comments with `body`."""
    pattern = _block_pattern(marker)
    if pattern.search(text) is None:
        raise ValueError(
            f"Could not find the '{marker}:start'/'{marker}:end' markers; "
            "add them around the generated lines."
        )
    # Substitute via a function so backslashes in `body` are taken literally
    # rather than read as group references.
    return pattern.sub(lambda m: m.group(1) + body + m.group(3), text, count=1)


def render_readme_coverage(coverage: dict[str, RaceCoverage]) -> str:
    """The bullet list under 'Data coverage' in the README."""
    men, women = coverage[MEN], coverage[WOMEN]
    return (
        f"-   **{men.name}**: {men.first_year} - {men.latest_year} "
        f"(all {men.editions} editions)\n"
        f"-   **{women.name}**: {women.first_year} - {women.latest_year} "
        "(all editions since the relaunch)"
    )


def render_docs_head(coverage: dict[str, RaceCoverage]) -> str:
    """The <title> and description meta tag of the docs page."""
    men, women = coverage[MEN], coverage[WOMEN]
    return (
        f"<title>Le Tour de France as CSV — {men.span_years} years of "
        "race data</title>\n"
        '<meta name="description" content="Every rider and every stage of the '
        f"Tour de France ({men.first_year}–{men.latest_year}) and the Tour de "
        f"France Femmes ({women.first_year}–{women.latest_year}) in four CSV "
        'files. Explore the data live.">'
    )


TARGETS: dict[str, Renderer] = {
    "README.md": render_readme_coverage,
    "docs/index.html": render_docs_head,
}


def sync_file(
    path: Path,
    coverage: dict[str, RaceCoverage],
    renderer: Renderer,
    write: bool = True,
) -> bool:
    """Sync one file. Returns True when the content was (or would be) changed."""
    original = path.read_text(encoding="utf-8")
    updated = replace_block(original, renderer(coverage))
    if updated == original:
        return False
    if write:
        path.write_text(updated, encoding="utf-8")
    return True


def sync_all(
    repo_root: Path, coverage: dict[str, RaceCoverage], write: bool = True
) -> dict[str, bool]:
    """Sync every target file, returning which ones changed."""
    return {
        relative: sync_file(repo_root / relative, coverage, renderer, write=write)
        for relative, renderer in TARGETS.items()
    }
