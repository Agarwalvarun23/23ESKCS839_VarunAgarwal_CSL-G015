"""Measure how expensive each scheme makes a single guess, and what that means
for an attacker.

Outputs (in results/):
    schemes.csv / schemes.png        hashes per second for the 6 main schemes
    crack_time.png                   projected time to try a 14.3M-word list
    pbkdf2_iterations.csv / .png     time per hash vs PBKDF2 iterations
    bcrypt_cost.csv / .png           time per hash vs bcrypt cost
    argon2_memory.csv / .png         time per hash vs Argon2 memory

Usage:
    python -m salting_demo.benchmark
"""

import csv
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write PNGs without opening a window
import matplotlib.pyplot as plt

from salting_demo.hashers import (Argon2Hasher, BcryptHasher, PBKDF2Hasher,
                                  default_hashers)

RESULTS = Path(__file__).resolve().parent.parent / "results"
PASSWORD = "sunshine"
ROCKYOU_WORDS = 14_344_391  # size of the well-known leaked wordlist


def time_per_hash(hasher, min_seconds=1.0, max_runs=200_000):
    """Average seconds per hash, running until min_seconds have passed."""
    runs = 0
    start = time.perf_counter()
    while True:
        hasher.hash(PASSWORD)
        runs += 1
        elapsed = time.perf_counter() - start
        if elapsed >= min_seconds or runs >= max_runs:
            return elapsed / runs


def human_time(seconds):
    for unit, size in (("years", 31_536_000), ("days", 86_400),
                       ("hours", 3_600), ("min", 60)):
        if seconds >= size:
            return f"{seconds / size:,.1f} {unit}"
    return f"{seconds:,.2f} s"


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def bench_schemes():
    print(f"{'Scheme':28} {'ms/hash':>10} {'hashes/s':>12} {'14.3M words':>16}")
    print("-" * 70)
    rows = []
    for h in default_hashers():
        t = time_per_hash(h)
        crack = t * ROCKYOU_WORDS
        rows.append([h.name, t * 1000, 1 / t, crack])
        print(f"{h.name:28} {t*1000:>10.4f} {1/t:>12,.0f} {human_time(crack):>16}")
    write_csv(RESULTS / "schemes.csv",
              ["scheme", "ms_per_hash", "hashes_per_sec", "seconds_for_rockyou"], rows)

    names = [r[0] for r in rows]
    colors = ["#c0392b"] * 3 + ["#27ae60"] * 3  # fast = red, slow = green

    plt.figure(figsize=(10, 5))
    plt.bar(names, [r[2] for r in rows], color=colors)
    plt.yscale("log")
    plt.ylabel("Hashes per second (log scale)")
    plt.title("Attacker guess rate per scheme (single CPU core)")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(RESULTS / "schemes.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(names, [r[3] for r in rows], color=colors)
    plt.yscale("log")
    plt.ylabel("Seconds (log scale)")
    plt.title(f"Time to try all {ROCKYOU_WORDS:,} rockyou words against ONE hash")
    for i, r in enumerate(rows):
        plt.text(i, r[3], human_time(r[3]), ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(RESULTS / "crack_time.png", dpi=150)
    plt.close()


def bench_param(title, label, values, make, filename, min_seconds=0.5):
    print(f"\n{title}")
    rows = []
    for v in values:
        t = time_per_hash(make(v), min_seconds=min_seconds, max_runs=50)
        rows.append([v, t * 1000])
        print(f"  {label}={v:<10} {t*1000:>10.2f} ms/hash")
    write_csv(RESULTS / f"{filename}.csv", [label, "ms_per_hash"], rows)

    plt.figure(figsize=(7, 4.5))
    plt.plot([r[0] for r in rows], [r[1] for r in rows], marker="o")
    plt.xlabel(label)
    plt.ylabel("Milliseconds per hash")
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULTS / f"{filename}.png", dpi=150)
    plt.close()


def main():
    RESULTS.mkdir(exist_ok=True)
    bench_schemes()
    bench_param("PBKDF2-SHA256: time vs iterations", "iterations",
                [10_000, 100_000, 300_000, 600_000, 1_000_000],
                PBKDF2Hasher, "pbkdf2_iterations")
    bench_param("bcrypt: time vs cost factor (each +1 doubles work)", "cost",
                [8, 10, 12, 14], BcryptHasher, "bcrypt_cost")
    bench_param("Argon2id: time vs memory (t=3, p=4)", "memory_MiB",
                [8, 16, 32, 64, 128, 256],
                lambda mib: Argon2Hasher(memory_kib=mib * 1024), "argon2_memory")
    print(f"\nSaved CSVs and graphs to {RESULTS}")


if __name__ == "__main__":
    main()
