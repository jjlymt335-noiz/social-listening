from app.pipeline.text_clean import clean_text


def test_removes_urls():
    assert "check " == clean_text("check https://example.com ")


def test_removes_mentions():
    assert "hello world" == clean_text("hello @user world")


def test_keeps_hashtag_words():
    assert "travel" == clean_text("#travel")


def test_removes_html():
    assert "hello" == clean_text("<b>hello</b>")


def test_collapses_whitespace():
    assert "a b c" == clean_text("a   b   c")
