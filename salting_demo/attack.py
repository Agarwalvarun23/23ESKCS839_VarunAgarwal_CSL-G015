"""Offline dictionary and brute-force attacks against stolen password hashes.

Scenario: an attacker has stolen the stored hashes (a "leaked database") and
tries guesses offline. All passwords here are dummy test data.

Usage:
    python -m salting_demo.attack                  # dictionary attack, all schemes
    python -m salting_demo.attack --brute 4        # also brute-force up to 4 chars
"""

import argparse
import itertools
import json
import string
import time
from pathlib import Path

from salting_demo.hashers import default_hashers

DATA = Path(__file__).resolve().parent.parent / "data"


def load_users():
    return json.loads((DATA / "users.json").read_text(encoding="utf-8"))


def load_wordlist():
    return (DATA / "wordlist.txt").read_text(encoding="utf-8").split()


def build_leak(hasher, users):
    """Simulate the stolen database: username -> stored hash."""
    return {u["username"]: hasher.hash(u["password"]) for u in users}


def dictionary_attack(hasher, leak, wordlist, time_limit=None):
    """Try every word against every stored hash.

    Returns (cracked dict, guesses made, seconds taken, finished?).
    """
    cracked, guesses = {}, 0
    start = time.perf_counter()
    for user, stored in leak.items():
        for word in wordlist:
            if time_limit and time.perf_counter() - start > time_limit:
                return cracked, guesses, time.perf_counter() - start, False
            guesses += 1
            if hasher.verify(word, stored):
                cracked[user] = word
                break
    return cracked, guesses, time.perf_counter() - start, True


def brute_force_candidates(max_len, charset=string.ascii_lowercase):
    """All strings of length 1..max_len over charset (a, b, ..., zzzz)."""
    for length in range(1, max_len + 1):
        for combo in itertools.product(charset, repeat=length):
            yield "".join(combo)


def brute_force_attack(hasher, stored, max_len, time_limit=None):
    """Brute-force a single stored hash. Returns (password|None, guesses, secs, finished?)."""
    guesses = 0
    start = time.perf_counter()
    for cand in brute_force_candidates(max_len):
        if time_limit and time.perf_counter() - start > time_limit:
            return None, guesses, time.perf_counter() - start, False
        guesses += 1
        if hasher.verify(cand, stored):
            return cand, guesses, time.perf_counter() - start, True
    return None, guesses, time.perf_counter() - start, True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--time-limit", type=float, default=60,
                    help="max seconds per scheme (default 60)")
    ap.add_argument("--brute", type=int, default=0,
                    help="also brute-force a short password up to N lowercase chars")
    args = ap.parse_args()

    users, wordlist = load_users(), load_wordlist()
    print(f"Users: {len(users)}   Wordlist: {len(wordlist)} words\n")
    print(f"{'Scheme':28} {'Cracked':>8} {'Guesses':>8} {'Time (s)':>10} {'Guesses/s':>12}")
    print("-" * 70)

    for h in default_hashers():
        leak = build_leak(h, users)
        cracked, guesses, secs, done = dictionary_attack(h, leak, wordlist, args.time_limit)
        rate = guesses / secs if secs else float("inf")
        note = "" if done else "  (time limit hit)"
        print(f"{h.name:28} {len(cracked):>5}/{len(users)} {guesses:>8} "
              f"{secs:>10.3f} {rate:>12,.0f}{note}")
        for user, pw in cracked.items():
            print(f"    {user:8} -> {pw}")

    if args.brute:
        target = "dog"  # dummy short password
        print(f"\nBrute force: target '{target}', charset a-z, length 1..{args.brute}")
        print(f"{'Scheme':28} {'Found':>8} {'Guesses':>10} {'Time (s)':>10}")
        print("-" * 60)
        for h in default_hashers():
            pw, guesses, secs, done = brute_force_attack(h, h.hash(target),
                                                         args.brute, args.time_limit)
            found = pw if pw else ("-" if done else "timeout")
            print(f"{h.name:28} {found:>8} {guesses:>10,} {secs:>10.3f}")


if __name__ == "__main__":
    main()
