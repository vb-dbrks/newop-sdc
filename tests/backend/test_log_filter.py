import logging

from backend.log_filter import RedactingFilter


def test_redacts_email_and_token(caplog):
    logger = logging.getLogger("velocia.test")
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.INFO, logger="velocia.test"):
        logger.info("user alice@example.com used token dapi1234567890abcdef1234567890abcdef")  # gitleaks:allow — synthetic fixture for redaction filter test
    msg = caplog.records[-1].getMessage()
    assert "alice@example.com" not in msg
    assert "dapi1234567890abcdef" not in msg
    assert "<email>" in msg
    assert "<token>" in msg
