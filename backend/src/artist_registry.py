"""Canonical artist definitions for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ArtistDefinition:
    slug: str
    display_name: str
    search_query: str

REGISTERED_ARTISTS: List[ArtistDefinition] = [
    ArtistDefinition(slug="blackpink", display_name="BLACKPINK", search_query="블랙핑크,BLACKPINK"),
    ArtistDefinition(slug="bts", display_name="BTS", search_query="방탄소년단,BTS"),
    ArtistDefinition(slug="ive", display_name="IVE", search_query="아이브,IVE"),
    ArtistDefinition(slug="straykids", display_name="Stray Kids", search_query="스트레이키즈,Stray Kids"),
    ArtistDefinition(slug="aespa", display_name="aespa", search_query="에스파,aespa"),
    ArtistDefinition(slug="babymonster", display_name="BABYMONSTER", search_query="베이비몬스터,BABYMONSTER"),
    ArtistDefinition(slug="newjeans", display_name="NewJeans", search_query="뉴진스,NewJeans"),
    ArtistDefinition(slug="enhypen", display_name="ENHYPEN", search_query="엔하이픈,ENHYPEN"),
]


_ARTISTS: Dict[str, ArtistDefinition] = {}
for definition in REGISTERED_ARTISTS:
    keys = {definition.display_name.upper(), definition.slug.upper()}
    for token in definition.search_query.split(","):
        keys.add(token.strip().upper())
    for key in keys:
        _ARTISTS[key] = definition


def get_artist_definition(name: str) -> ArtistDefinition:
    key = name.strip().upper()
    if key not in _ARTISTS:
        raise KeyError(name)
    return _ARTISTS[key]


def list_registered_artists() -> List[str]:
    return [definition.display_name for definition in REGISTERED_ARTISTS]
