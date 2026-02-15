"""ISO 3166-1 alpha-2 country code to region group mapping.

Every country code must appear in exactly one group.
Validated at startup via validate_no_duplicate_codes().
"""

FEATURED = {
    "JP": "JAPAN",
    "KR": "KOREA",
    "TH": "THAILAND",
}

REGION_GROUPS: dict[str, list[str]] = {
    "EAST_ASIA_OTHER": ["CN", "HK", "MO", "TW", "MN", "KP"],
    "SEA_OTHER": ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "VN", "TL"],
    "SOUTH_ASIA_OTHER": ["AF", "BD", "BT", "IN", "LK", "MV", "NP", "PK"],
    "CENTRAL_ASIA": ["KZ", "KG", "TJ", "TM", "UZ"],
    "WEST_ASIA_OTHER": [
        "AE", "AM", "AZ", "BH", "CY", "GE", "IL", "IQ", "IR",
        "JO", "KW", "LB", "OM", "PS", "QA", "SA", "SY", "TR", "YE",
    ],
}

FALLBACK_REGION = "ASIA_OTHER_UNMAPPED"


def _build_country_to_region() -> dict[str, str]:
    """Build a flat lookup: country_code -> region_group."""
    mapping: dict[str, str] = {}
    for code, region in FEATURED.items():
        mapping[code] = region
    for region, codes in REGION_GROUPS.items():
        for code in codes:
            mapping[code] = region
    return mapping


COUNTRY_TO_REGION: dict[str, str] = _build_country_to_region()


def get_region(country_code: str) -> str:
    """Return the region group for a country code, or FALLBACK."""
    return COUNTRY_TO_REGION.get(country_code.upper(), FALLBACK_REGION)


def validate_no_duplicate_codes() -> None:
    """Raise ValueError if any country code appears in more than one group."""
    seen: dict[str, str] = {}
    all_entries: list[tuple[str, str]] = []

    for code, region in FEATURED.items():
        all_entries.append((code, region))
    for region, codes in REGION_GROUPS.items():
        for code in codes:
            all_entries.append((code, region))

    for code, region in all_entries:
        if code in seen:
            raise ValueError(
                f"Duplicate country code '{code}': found in '{seen[code]}' and '{region}'"
            )
        seen[code] = region
