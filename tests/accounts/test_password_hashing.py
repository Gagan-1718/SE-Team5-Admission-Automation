from app.accounts.security import hash_password, verify_password


def test_same_password_gets_a_different_salted_hash_each_time():
    first = hash_password("fictional-password-123")
    second = hash_password("fictional-password-123")

    assert first != second
    assert first.startswith("scrypt:")
    assert second.startswith("scrypt:")


def test_correct_password_verifies_and_wrong_password_fails():
    stored_hash = hash_password("fictional-password-123")

    assert verify_password(stored_hash, "fictional-password-123") is True
    assert verify_password(stored_hash, "incorrect-password") is False


def test_plaintext_is_not_present_in_the_stored_hash():
    password = "fictional-password-123"

    assert password not in hash_password(password)


def test_malformed_hash_fails_without_exposing_an_error():
    assert verify_password("not-a-valid-hash", "anything") is False

