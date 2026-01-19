from core.security.hashing import hash_password, verify_password

def test_hash_and_verify_password():
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False
