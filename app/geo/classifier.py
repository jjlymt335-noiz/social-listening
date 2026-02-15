from app.geo.mappings import get_region


def classify_country(country_code: str) -> dict[str, str]:
    """Classify a country code into its region group.

    Returns dict with country_code and region_group.
    """
    code = country_code.upper().strip()
    return {
        "country_code": code,
        "region_group": get_region(code),
    }
