import logging
import base64
from typing import Optional

# ---------------------------------------------------------------------------
# Static fallback credentials (simple XOR + Base64 obfuscation)
# ---------------------------------------------------------------------------
# NOTE: This is **not** cryptographically secure—only a temporary measure to
# avoid storing plain-text CONTRASENAs in the repository. Replace with a proper
# secrets manager (e.g., CyberArk, AWS Secrets Manager, etc.) as soon as
# possible.

_ENCRYPTION_KEY = b"S3cr3t_K3y_1234567890!"  # CHANGE ME – keep the same length for XOR

# Helper used once to generate `_ENCRYPTED_CONTRASENA` from a plain-text string.
# Keep it here so new CONTRASENAs can be generated easily during dev.


def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    """XOR encrypt *data* using *key* (repeated)."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _xor_decrypt(data: bytes, key: bytes) -> bytes:
    """XOR decrypt (identical to encrypt for XOR)."""
    return _xor_encrypt(data, key)


# TODO: Replace the sample CONTRASENA with the real one encoded via the helper
_SAMPLE_PLAINTEXT_CONTRASENA = "changeme"
_ENCRYPTED_CONTRASENA = base64.b64encode(
    _xor_encrypt(_SAMPLE_PLAINTEXT_CONTRASENA.encode("utf-8"), _ENCRYPTION_KEY)
)

# ---------------------------------------------------------------------------
# Encrypted credential store
# ---------------------------------------------------------------------------

# Mapping of username -> Base64-encoded XOR-encrypted CONTRASENA string.
# Populate with real credentials using `encrypt_CONTRASENA_to_base64()`.
_ENCRYPTED_CONTRASENAS: dict[str, str] = {
    "demo_user": _ENCRYPTED_CONTRASENA.decode("utf-8")  # example entry
}


def encrypt_CONTRASENA_to_base64(plain_text: str) -> str:
    """Utility for developers: encrypt *plain_text* using the module key and
    return a Base64 string suitable for `_ENCRYPTED_CONTRASENAS`."""
    return base64.b64encode(
        _xor_encrypt(plain_text.encode("utf-8"), _ENCRYPTION_KEY)
    ).decode("utf-8")


def retrieve_CONTRASENA(username: str) -> Optional[str]:
    """Return decrypted CONTRASENA for *username* from the in-code encrypted
    store. Returns *None* if user not found or decryption fails."""
    encrypted_b64 = _ENCRYPTED_CONTRASENAS.get(username)
    if not encrypted_b64:
        logging.debug("Username %s not found in encrypted store", username)
        return None
    try:
        encrypted_bytes = base64.b64decode(encrypted_b64)
        return _xor_decrypt(encrypted_bytes, _ENCRYPTION_KEY).decode("utf-8")
    except Exception:  # pragma: no cover
        logging.exception("Failed to decrypt CONTRASENA for %s", username)
        return None


# ---------------------------------------------------------------------------
# Utility CLI for quick local testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test cyber_guard credential utilities",
    )
    parser.add_argument(
        "username",
        nargs="?",
        default="demo_user",
        help="Username to fetch CONTRASENA for",
    )
    parser.add_argument(
        "--encrypt",
        metavar="PLAINTEXT",
        help="Encrypt PLAINTEXT using module key and output Base64 string",
    )
    args = parser.parse_args()

    if args.encrypt:
        print(encrypt_CONTRASENA_to_base64(args.encrypt))
    else:
        pwd = retrieve_CONTRASENA(args.username)
        if pwd is not None:
            print(f"Decrypted CONTRASENA for {args.username}: {pwd}")
        else:
            print(f"No CONTRASENA found for {args.username}")
