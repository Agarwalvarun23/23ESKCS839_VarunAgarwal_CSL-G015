# CSL-G15 — Salting & Key Stretching Demonstrator

**Student:** Varun Agarwal (23ESKCS839), CS-D-G2
**Course:** Cyber Security Lab (7CS4-22) — Mini Project
**Linked experiment:** Exp 3 — Dictionary & Brute Force Attack
**Deadline:** 16 November 2026 (no extensions)
**Submission name:** `23ESKCS839_VarunAgarwal_CSL-G15`

## What we are building

A tool that shows how password storage choices change how fast an attacker can crack stolen hashes.

- **Salt**: random data added per user, so identical passwords get different hashes. This defeats precomputed rainbow tables.
- **Key stretching** (PBKDF2, bcrypt, Argon2): makes each hash deliberately slow, so a dictionary or brute-force attack costs far more.

The tool runs the same dictionary attack against test passwords stored six ways (MD5, SHA-256, salted SHA-256, PBKDF2, bcrypt, Argon2), measures the time, and presents tables, graphs and a live web demo.

All testing uses dummy passwords on the local machine only.

## Stages (stop after each stage and commit manually)

| # | Stage | Files | Output |
|---|---|---|---|
| 1 | Skeleton + hashers | `salting_demo/hashers.py`, `data/wordlist.txt`, `data/users.json`, `requirements.txt` | One interface for MD5, SHA-256, salted SHA-256, PBKDF2, bcrypt, Argon2 |
| 2 | Attacks | `salting_demo/attack.py` | Dictionary + small brute-force attack (≤4 lowercase chars); guesses and time |
| 3 | Rainbow / salt demo | `salting_demo/rainbow.py` | Precomputed table cracks unsalted hashes, fails on salted ones |
| 4 | Benchmarks + graphs | `salting_demo/benchmark.py`, `results/*.csv`, `results/*.png` | Hashes/sec per algorithm; PBKDF2 10k/100k/600k; bcrypt cost 10/12/14; Argon2 memory settings; projected time for a 14M-word list |
| 5 | Demo UI | `salting_demo/app.py` (Streamlit) | Enter password, pick algorithm, view hash/salt, run attack, compare timings |
| 6 | Run + screenshots | `screenshots/` | Labelled screenshots of each feature and result |
| 7 | Report + ZIP | `report/` (.docx, .pdf), submission .zip | Full report per guidelines + viva question list |

## Report structure (15–25 pages)

1. Front page (template)
2. Candidate's Declaration & Ethical Declaration (sign by hand)
3. Acknowledgement
4. Abstract (150–200 words)
5. Table of Contents
6. Ch 1 – Introduction: problem, objectives, link to Exp 3
7. Ch 2 – Background: hashing, dictionary/brute-force/rainbow attacks, salt, PBKDF2, bcrypt, Argon2
8. Ch 3 – Tools & Environment: hardware, OS, Python, libraries
9. Ch 4 – Codes
10. Ch 5 – Results & Testing: screenshots, test cases, tables, graphs
11. Ch 6 – Conclusion & Future Scope

**Formatting:** A4, Times New Roman; headings 16 pt bold, sub-headings 14 pt bold, body 12 pt; 1.5 spacing; justified; page numbers bottom centre; numbered figures/tables; code in Consolas 10 pt.

## Manual tasks

- Sign the declarations
- Print the report
- Read and understand every line of code for the viva (25% of marks)
- Submit to Vikash (vikash@skit.ac.in) by 16 Nov 2026
