from app.geo.classifier import classify_country
from app.geo.mappings import FALLBACK_REGION, validate_no_duplicate_codes


def test_featured_countries():
    assert classify_country("JP") == {"country_code": "JP", "region_group": "JAPAN"}
    assert classify_country("KR") == {"country_code": "KR", "region_group": "KOREA"}
    assert classify_country("TH") == {"country_code": "TH", "region_group": "THAILAND"}


def test_region_groups():
    assert classify_country("CN")["region_group"] == "EAST_ASIA_OTHER"
    assert classify_country("SG")["region_group"] == "SEA_OTHER"
    assert classify_country("IN")["region_group"] == "SOUTH_ASIA_OTHER"
    assert classify_country("KZ")["region_group"] == "CENTRAL_ASIA"
    assert classify_country("AE")["region_group"] == "WEST_ASIA_OTHER"


def test_fallback():
    result = classify_country("US")
    assert result["region_group"] == FALLBACK_REGION


def test_case_insensitive():
    assert classify_country("jp")["region_group"] == "JAPAN"


def test_no_duplicate_codes():
    # Should not raise
    validate_no_duplicate_codes()
