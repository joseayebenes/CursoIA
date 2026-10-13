"""The invented project of the course: requirements, documents and Ada code (see
datos/README.md)."""
from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "datos"


def requirements() -> list[dict]:
    """The requirements, as exported from DOORS: id, module, heading, text, verification."""
    with open(DATA / "requisitos.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def documents() -> dict[str, str]:
    """The documents by file name: the design (English) and the operator manual (Spanish)."""
    return {p.name: p.read_text("utf-8") for p in sorted((DATA / "documentos").glob("*.md"))}


def ada_sources() -> dict[str, str]:
    """The Ada sources by path relative to datos/ada: src/ and tests/."""
    root = DATA / "ada"
    return {p.relative_to(root).as_posix(): p.read_text("utf-8")
            for p in sorted(root.glob("*/*.ad[sb]"))}
