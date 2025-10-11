"""Canonical artist definitions for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ArtistDefinition:
    slug: str
    display_name: str


_ARTISTS: Dict[str, ArtistDefinition] = {
    "BLACKPINK": ArtistDefinition(slug="blackpink", display_name="BLACKPINK"),
    "IVE": ArtistDefinition(slug="ive", display_name="IVE"),
    "BTS": ArtistDefinition(slug="bts", display_name="BTS"),
}


def get_artist_definition(name: str) -> ArtistDefinition:
    key = name.strip().upper()
    return _ARTISTS[key]
