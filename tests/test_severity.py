from app.engine.severity import compute_severity


def test_p0():
    assert compute_severity(cluster_size=51, neg_ratio=0.75) == "P0"


def test_p0_requires_both_conditions():
    # High size but low neg_ratio -> P1, not P0
    assert compute_severity(cluster_size=51, neg_ratio=0.5) == "P1"


def test_p1():
    assert compute_severity(cluster_size=25, neg_ratio=0.3) == "P1"


def test_p2():
    assert compute_severity(cluster_size=10, neg_ratio=0.5) == "P2"


def test_boundary_p1():
    # Exactly 20 is not > 20
    assert compute_severity(cluster_size=20, neg_ratio=0.5) == "P2"
    assert compute_severity(cluster_size=21, neg_ratio=0.5) == "P1"
