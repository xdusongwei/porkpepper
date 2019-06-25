import porkpepper.utils


def test_hash_cipher():
    cipher = porkpepper.utils.HashCipher()
    digest_result = cipher.digest("asdfg")
    hex_result = cipher.hash("asdfg")
    digest_target = b"\x1f1\xb6>&\xcdA\x02\x8b'\x8e\x1d\x9d\x8ch\x1eC\xac\xf4J~\xf5\xc6$\x86\x9a\x06\x7f\x1eF\x84\xee" \
                    b"!1gc>\x87LZ\x9dwrB\xbb\xdd\xea!l\xc8\xc1O\x849o\xf9ya\xef\xc5\xda\xd4d\xc7"
    hex_target = "1f31b63e26cd41028b278e1d9d8c681e43acf44a7ef5c624869a067f1e4684ee213167633e874c5a9d777242bbddea216cc" \
                 "8c14f84396ff97961efc5dad464c7"
    assert digest_result == digest_target
    assert hex_result == hex_target


def test_create_key():
    key = porkpepper.utils.create_base58_key("asdfg", length=8, prefix="TEST")
    assert len(key) == 4 + 8
    assert key == "TESTdB2qSkJY"
