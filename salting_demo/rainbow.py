"""Why salt matters: precomputed tables vs salted hashes.

A precomputed table maps hash -> password for every word in a wordlist. It is
built ONCE, then any leaked unsalted hash can be cracked by a single lookup.
(A real rainbow table stores hash chains instead of every pair to save space,
but the effect is the same: work is done before the leak, not after.)

Salt breaks this: each user's hash depends on a random salt, so the table
would have to be rebuilt for every possible salt (2^128 of them here).

Usage:
    python -m salting_demo.rainbow
"""

import time

from salting_demo.attack import load_users, load_wordlist
from salting_demo.hashers import MD5Hasher, SaltedSHA256Hasher, SHA256Hasher


def build_table(hasher, wordlist):
    """Precompute hash -> password for an unsalted hasher."""
    return {hasher.hash(w): w for w in wordlist}


def lookup_attack(table, leak):
    """Crack a leaked database with dictionary lookups only (no hashing)."""
    return {user: table[h] for user, h in leak.items() if h in table}


def show_leak(title, leak):
    print(title)
    for user, h in leak.items():
        print(f"    {user:8} {h}")


def main():
    users, wordlist = load_users(), load_wordlist()

    # 1. Same password -> same hash when there is no salt.
    print("=" * 78)
    print("1. Identical passwords (alice and dave both use 'password')")
    print("=" * 78)
    sha, salted = SHA256Hasher(), SaltedSHA256Hasher()
    unsalted_leak = {u["username"]: sha.hash(u["password"]) for u in users}
    salted_leak = {u["username"]: salted.hash(u["password"]) for u in users}
    show_leak("Unsalted SHA-256 (alice == dave, visible in the leak):", unsalted_leak)
    print(f"  -> alice == dave ? {unsalted_leak['alice'] == unsalted_leak['dave']}\n")
    show_leak("Salted SHA-256 (salt$hash):", salted_leak)
    print(f"  -> alice == dave ? {salted_leak['alice'] == salted_leak['dave']}\n")

    # 2. Precomputed table cracks unsalted leaks instantly, fails on salted.
    print("=" * 78)
    print("2. Precomputed table attack")
    print("=" * 78)
    for hasher in (MD5Hasher(), SHA256Hasher()):
        t0 = time.perf_counter()
        table = build_table(hasher, wordlist)
        build_secs = time.perf_counter() - t0

        leak = {u["username"]: hasher.hash(u["password"]) for u in users}
        t0 = time.perf_counter()
        cracked = lookup_attack(table, leak)
        lookup_secs = time.perf_counter() - t0
        print(f"{hasher.name:8} table: {len(table)} entries built in {build_secs*1000:.2f} ms; "
              f"cracked {len(cracked)}/{len(users)} in {lookup_secs*1e6:.1f} us")
        for user, pw in cracked.items():
            print(f"    {user:8} -> {pw}")

    # Try the same idea on salted hashes: build the table with no salt and look up.
    table = build_table(sha, wordlist)
    salted_digests = {u: h.split("$")[1] for u, h in salted_leak.items()}
    cracked = lookup_attack(table, salted_digests)
    print(f"\nSHA-256 table vs SALTED leak: cracked {len(cracked)}/{len(users)}")
    print("  -> table is useless; attacker must hash every guess per user, per salt.")

    # 3. Cost of precomputing for salts.
    print("\n" + "=" * 78)
    print("3. Table size needed to cover salts")
    print("=" * 78)
    words = len(wordlist)
    for bits in (0, 8, 16, 32, 128):
        print(f"  {bits:>3}-bit salt: {words} words x 2^{bits} salts = {words * 2**bits:.3e} entries")


if __name__ == "__main__":
    main()
