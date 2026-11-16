# Salting & Key Stretching Demonstrator (CSL-G15)

Varun Agarwal (23ESKCS839), CS-D-G2. This is a mini project for Cyber Security Lab (7CS4-22) and is linked to Exp 3 (Dictionary & Brute Force Attack).

It shows how salting and key stretching (PBKDF2, bcrypt, Argon2id) slow down dictionary, brute-force and precomputed-table attacks on stolen password hashes. All passwords are dummy test data, and everything runs locally.

## Setup

```bash
pip install -r requirements.txt
```

## Run

| Command | What it does |
|---|---|
| `python -m salting_demo.attack --brute 3` | Dictionary + brute-force attack on all 6 schemes |
| `python -m salting_demo.rainbow` | Precomputed table vs salted hashes |
| `python -m salting_demo.benchmark` | Timings, CSVs and graphs in `results/` |
| `streamlit run salting_demo/app.py` | Interactive demo at http://localhost:8501 |

## Layout

- `salting_demo/`: project source code (`hashers.py`, `attack.py`, `rainbow.py`, `benchmark.py`, `app.py`)
- `data/`: dummy users and the test wordlist
- `results/`: benchmark CSVs and graphs
- `screenshots/`: images used in the report
- `tools/`: scripts that produce the screenshots, the report and the ZIP (these need extra packages: `playwright`, `python-docx`, `pywin32`, `pymupdf`)
- `report/`: the report (DOCX and PDF)
