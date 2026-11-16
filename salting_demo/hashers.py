"""Password hashing schemes compared in this project.

Every scheme exposes the same two functions:
    hash(password)            -> stored string (includes salt/params if any)
    verify(password, stored)  -> True if password matches

so the attack and benchmark code can treat all of them the same way.
"""

import hashlib
import hmac
import os

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class Hasher:
    name = "base"
    salted = False

    def hash(self, password: str) -> str:
        raise NotImplementedError

    def verify(self, password: str, stored: str) -> bool:
        raise NotImplementedError


# ---------- Fast, unsalted (insecure) ----------

class MD5Hasher(Hasher):
    name = "MD5"

    def hash(self, password):
        return hashlib.md5(password.encode()).hexdigest()

    def verify(self, password, stored):
        return hmac.compare_digest(self.hash(password), stored)


class SHA256Hasher(Hasher):
    name = "SHA-256"

    def hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, password, stored):
        return hmac.compare_digest(self.hash(password), stored)


# ---------- Fast, salted ----------

class SaltedSHA256Hasher(Hasher):
    """Stored as 'salt_hex$hash_hex'. Salt is 16 random bytes per password."""
    name = "SHA-256 + salt"
    salted = True

    def hash(self, password, salt: bytes = None):
        salt = salt or os.urandom(16)
        digest = hashlib.sha256(salt + password.encode()).hexdigest()
        return f"{salt.hex()}${digest}"

    def verify(self, password, stored):
        salt_hex, _ = stored.split("$")
        return hmac.compare_digest(self.hash(password, bytes.fromhex(salt_hex)), stored)


# ---------- Slow, salted (key stretching) ----------

class PBKDF2Hasher(Hasher):
    """PBKDF2-HMAC-SHA256. Stored as 'iterations$salt_hex$hash_hex'."""
    salted = True

    def __init__(self, iterations=600_000):
        self.iterations = iterations
        self.name = f"PBKDF2 ({iterations:,} it)"

    def hash(self, password, salt: bytes = None):
        salt = salt or os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.iterations)
        return f"{self.iterations}${salt.hex()}${dk.hex()}"

    def verify(self, password, stored):
        iters, salt_hex, _ = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(f"{iters}${salt_hex}${dk.hex()}", stored)


class BcryptHasher(Hasher):
    """bcrypt stores cost and salt inside its own output string ($2b$12$...).

    bcrypt only uses the first 72 bytes of a password, and the library raises
    an error for longer input, so we truncate explicitly (standard practice).
    """
    salted = True
    MAX_BYTES = 72

    def __init__(self, cost=12):
        self.cost = cost
        self.name = f"bcrypt (cost {cost})"

    def _encode(self, password):
        return password.encode()[:self.MAX_BYTES]

    def hash(self, password):
        return bcrypt.hashpw(self._encode(password), bcrypt.gensalt(self.cost)).decode()

    def verify(self, password, stored):
        return bcrypt.checkpw(self._encode(password), stored.encode())


class Argon2Hasher(Hasher):
    """Argon2id: memory-hard. memory_kib is RAM used per hash."""
    salted = True

    def __init__(self, time_cost=3, memory_kib=65536, parallelism=4):
        self.ph = PasswordHasher(time_cost=time_cost, memory_cost=memory_kib,
                                 parallelism=parallelism)
        self.name = f"Argon2id (t={time_cost}, m={memory_kib // 1024} MiB)"

    def hash(self, password):
        return self.ph.hash(password)

    def verify(self, password, stored):
        try:
            return self.ph.verify(stored, password)
        except VerifyMismatchError:
            return False


def default_hashers():
    """The six schemes compared throughout the project."""
    return [
        MD5Hasher(),
        SHA256Hasher(),
        SaltedSHA256Hasher(),
        PBKDF2Hasher(600_000),
        BcryptHasher(12),
        Argon2Hasher(),
    ]
