"""Run each command-line script and save its console output as a PNG
(terminal-style image) for the report.

Usage:
    python tools/cli_screenshots.py
"""

import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"

RUNS = [
    ("cli_attack.png", "python -m salting_demo.attack --brute 3 --time-limit 20",
     [sys.executable, "-m", "salting_demo.attack", "--brute", "3", "--time-limit", "20"]),
    ("cli_rainbow.png", "python -m salting_demo.rainbow",
     [sys.executable, "-m", "salting_demo.rainbow"]),
]


def render(text, title, path):
    lines = text.rstrip().splitlines()
    height = 0.6 + 0.165 * (len(lines) + 2)
    fig = plt.figure(figsize=(11, height), facecolor="#1e1e1e")
    fig.text(0.01, 1 - 0.25 / height, f"PS D:\\project\\23ESKCS839_VarunAg_CS-Project> {title}",
             family="Consolas", size=9, color="#4ec9b0", va="top")
    fig.text(0.01, 1 - 0.55 / height, "\n".join(lines),
             family="Consolas", size=9, color="#d4d4d4", va="top", linespacing=1.35)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    for name, title, cmd in RUNS:
        print("Running:", title)
        text = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
        render(text, title, OUT / name)
    bench = (ROOT / "results" / "benchmark_output.txt").read_text()
    render(bench, "python -m salting_demo.benchmark", OUT / "cli_benchmark.png")
    print("Saved to", OUT)


if __name__ == "__main__":
    main()
