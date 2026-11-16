"""Build the project report (DOCX + PDF) following the SKIT guidelines.

Numbers in the results chapter are read from results/*.csv, so re-running the
benchmark and then this script keeps the report consistent.

Usage:
    python tools/build_report.py
"""

import ast
import csv
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
SHOTS = ROOT / "screenshots"
OUT_DIR = ROOT / "report"
BASENAME = "23ESKCS839_VarunAgarwal_CSL-G15"

NAME, ROLL, BATCH = "Varun Agarwal", "23ESKCS839", "CS-D-G2"
CODE = "CSL-G15"
TITLE = "Salting & Key Stretching Demonstrator"
NAVY = RGBColor(0x1F, 0x38, 0x64)

fig_no = {}  # chapter -> running figure count
tab_no = {}


# ---------------------------------------------------------------- helpers

def read_csv(name):
    with open(RESULTS / name) as f:
        return list(csv.DictReader(f))


def human_time(seconds):
    for unit, size in (("years", 31_536_000), ("days", 86_400),
                       ("hours", 3_600), ("min", 60)):
        if seconds >= size:
            return f"{seconds / size:,.1f} {unit}"
    return f"{seconds:,.1f} s"


def set_cell_shading(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def add_field(paragraph, instr):
    """Insert a Word field (PAGE, TOC ...). Word fills it on update."""
    run = paragraph.add_run()
    for tag, text in (("begin", None), (None, instr), ("separate", None), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def para(doc, text="", bold=False, italic=False, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         color=None, space_after=6, style=None):
    p = doc.add_paragraph(style=style)
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        r.bold, r.italic, r.font.size = bold, italic, Pt(size)
        if color:
            r.font.color.rgb = color
    return p


def rich(doc, parts, align=WD_ALIGN_PARAGRAPH.JUSTIFY, style=None):
    """parts: list of (text, bold) tuples in one paragraph."""
    p = doc.add_paragraph(style=style)
    p.alignment = align
    for text, bold in parts:
        p.add_run(text).bold = bold
    return p


def bullets(doc, items):
    for item in items:
        if isinstance(item, tuple):
            rich(doc, [(item[0], True), (item[1], False)], style="List Bullet")
        else:
            para(doc, item, style="List Bullet", space_after=2)


def heading(doc, text, level, new_page=False):
    h = doc.add_heading(text, level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # page_break_before avoids the blank page a separate page-break
    # paragraph leaves when the previous page is exactly full.
    h.paragraph_format.page_break_before = new_page
    return h


def title_page_heading(doc, text):
    p = para(doc, text, bold=True, size=16, color=NAVY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    p.paragraph_format.page_break_before = True
    return p


def chapter(doc, number, title):
    heading(doc, f"Chapter {number} – {title}", 1, new_page=True)


def figure_pair(doc, chapter_no, items, width_cm=7.8):
    """Two figures side by side, each with its own number and caption."""
    t = doc.add_table(rows=2, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for col, (path, caption) in enumerate(items):
        fig_no[chapter_no] = fig_no.get(chapter_no, 0) + 1
        img_p = t.rows[0].cells[col].paragraphs[0]
        img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_p.paragraph_format.keep_with_next = True
        img_p.add_run().add_picture(str(path), width=Cm(width_cm))
        cap_p = t.rows[1].cells[col].paragraphs[0]
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p.paragraph_format.line_spacing = 1.0
        r = cap_p.add_run(f"Fig. {chapter_no}.{fig_no[chapter_no]}: {caption}")
        r.italic, r.font.size = True, Pt(10)
    para(doc, "", space_after=4)


def figure(doc, chapter_no, path, caption, width_cm=15.5):
    fig_no[chapter_no] = fig_no.get(chapter_no, 0) + 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    c = para(doc, f"Fig. {chapter_no}.{fig_no[chapter_no]}: {caption}", italic=True, size=10,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    return c


def table(doc, chapter_no, caption, header, rows, widths_cm):
    tab_no[chapter_no] = tab_no.get(chapter_no, 0) + 1
    c = para(doc, f"Table {chapter_no}.{tab_no[chapter_no]}: {caption}", italic=True, size=10,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    c.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(h)
        r.bold, r.font.size = True, Pt(11)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(cell, "1F3864")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(v)).font.size = Pt(11)
    for row in t.rows:
        for i, w in enumerate(widths_cm):
            row.cells[i].width = Cm(w)
        for cell in row.cells:
            pf = cell.paragraphs[0].paragraph_format
            pf.line_spacing, pf.space_after = 1.0, Pt(0)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    para(doc, "", space_after=4)


def code_block(doc, source):
    for line in source.rstrip().splitlines():
        p = doc.add_paragraph(style="Code")
        p.add_run(line if line else " ")


def source_of(path, names):
    """Return the source of selected top-level functions/classes from a file."""
    text = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()
    parts = []
    for node in tree.body:
        if getattr(node, "name", None) in names:
            start = (node.decorator_list[0].lineno if getattr(node, "decorator_list", None)
                     else node.lineno) - 1
            parts.append("\n".join(lines[start:node.end_lineno]))
    return "\n\n\n".join(parts)


# ---------------------------------------------------------------- document setup

def setup(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.54)
    sec.top_margin = sec.bottom_margin = Cm(2.54)

    st = doc.styles
    normal = st["Normal"]
    normal.font.name = "Times New Roman"
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
        s = st[name]
        s.font.name, s.font.size, s.font.bold = "Times New Roman", Pt(size), True
        s.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
        s.font.color.rgb = NAVY if name == "Heading 1" else RGBColor(0, 0, 0)
        s.font.italic = False
        s.paragraph_format.space_before = Pt(18 if name == "Heading 1" else 12)
        s.paragraph_format.space_after = Pt(8)
        s.paragraph_format.keep_with_next = True
        s.paragraph_format.line_spacing = 1.15

    lb = st["List Bullet"]
    lb.font.name, lb.font.size = "Times New Roman", Pt(12)
    lb.paragraph_format.space_after = Pt(2)

    code = st.add_style("Code", 1)
    code.font.name, code.font.size = "Consolas", Pt(10)
    code.element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    pf = code.paragraph_format
    pf.line_spacing, pf.space_after, pf.space_before = 1.0, Pt(0), Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.left_indent = Cm(0.3)

    # Footer: page number at bottom centre (front page excluded below)
    sec.different_first_page_header_footer = True
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(fp, "PAGE")


# ---------------------------------------------------------------- front matter

def front_page(doc):
    c = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, "A", size=14, align=c, space_after=2)
    para(doc, "Mini Project Report", bold=True, size=20, align=c, space_after=2)
    para(doc, "on", size=14, align=c, space_after=2)
    para(doc, f"“{TITLE.upper()}”", bold=True, size=20, align=c, color=NAVY, space_after=2)
    para(doc, f"Project Code: {CODE}", size=13, align=c, space_after=12)
    para(doc, "Submitted in partial fulfilment of the requirements of", italic=True, size=13,
         align=c, space_after=0)
    para(doc, "Cyber Security Lab (7CS4-22)", bold=True, size=15, align=c, space_after=0)
    para(doc, "Bachelor of Technology — VII Semester", size=13, align=c, space_after=0)
    para(doc, "in", size=13, align=c, space_after=0)
    para(doc, "Computer Science & Engineering", bold=True, size=14, align=c, space_after=0)
    para(doc, "Session 2026-27", size=13, align=c, space_after=10)

    p = doc.add_paragraph()
    p.alignment = c
    p.add_run().add_picture(str(OUT_DIR / "assets" / "skit_logo.png"), width=Cm(4.2))

    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    left = [("Submitted By:", True, NAVY), (f"Name: {NAME}", False, None),
            (f"Roll No.: {ROLL}", False, None), (f"Class / Batch: {BATCH}", False, None),
            ("Semester: VII", False, None)]
    right = [("Submitted To:", True, NAVY), ("Vikash Dhankar", False, None),
             ("Assistant Professor", False, None), ("Department of CSE", False, None),
             ("SKIT, Jaipur", False, None)]
    for cell, lines in zip(t.rows[0].cells, (left, right)):
        cell.width = Cm(8)
        cell.paragraphs[0].text = ""
        for i, (text, bold, color) in enumerate(lines):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing, p.paragraph_format.space_after = 1.15, Pt(0)
            label, _, value = text.partition(": ")
            if value and not bold:
                r = p.add_run(label + ": ")
                r.bold = True
                p.add_run(value)
            else:
                r = p.add_run(text)
                r.bold = bold
                if color:
                    r.font.color.rgb = color
                    r.font.size = Pt(13)

    para(doc, "", space_after=14)
    para(doc, "Department of Computer Science & Engineering", bold=True, size=13, align=c,
         color=NAVY, space_after=0)
    para(doc, "Swami Keshvanand Institute of Technology, Management & Gramothan, Jaipur",
         bold=True, size=13, align=c, space_after=0)
    para(doc, "(Affiliated to Rajasthan Technical University, Kota)", size=11, align=c,
         space_after=0)
    para(doc, "November 2026", bold=True, size=13, align=c, space_after=0)


def declarations(doc):
    title_page_heading(doc, "CANDIDATE'S DECLARATION")
    para(doc, f"I, {NAME}, Roll No. {ROLL}, a student of B.Tech VII Semester, CSE, {BATCH}, "
              f"hereby declare that the mini project titled “{TITLE}” (Project Code {CODE}) "
              "submitted for the Cyber Security Lab (7CS4-22) is my own original work, carried "
              "out under the guidance of Vikash, Assistant Professor, Department of CSE, SKIT "
              "Jaipur. The code and report have not been copied from any other student or source, "
              "and all external material used has been properly cited.")
    para(doc, "ETHICAL DECLARATION", bold=True, size=16, color=NAVY,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    para(doc, "I declare that all attack, sniffing, scanning or testing activities performed in "
              "this project were carried out only on my own systems, virtual machines or an "
              "isolated lab environment, using test data. No unauthorised system, network, "
              "account or person was targeted. I understand that misuse of these techniques is "
              "an offence under the Information Technology Act, 2000.")
    para(doc, "", space_after=30)
    t = doc.add_table(rows=2, cols=2)
    t.rows[0].cells[0].text = "Date: ____________"
    t.rows[0].cells[1].text = "______________________"
    t.rows[1].cells[0].text = "Place: Jaipur"
    t.rows[1].cells[1].text = f"Signature of Student\n{NAME} ({ROLL})"
    for row in t.rows:
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for cell in row.cells:
            cell.paragraphs[0].paragraph_format.line_spacing = 1.15


def acknowledgement(doc):
    title_page_heading(doc, "ACKNOWLEDGEMENT")
    para(doc, "I would like to express my sincere gratitude to Mr. Vikash Dhankar, Assistant "
              "Professor, Department of Computer Science & Engineering, SKIT Jaipur, for his "
              "guidance throughout the Cyber Security Lab and for designing this mini project, "
              "which connected the dictionary and brute-force attack experiment to the defensive "
              "techniques used in real systems.")
    para(doc, "I am also thankful to the Head of the Department and the faculty of the "
              "Department of Computer Science & Engineering for providing the facilities and "
              "environment needed to complete this work, and to the developers of the open-source "
              "Python libraries (bcrypt, argon2-cffi, Matplotlib and Streamlit) used in this "
              "project.")
    para(doc, "Finally, I thank my family and friends for their constant support and "
              "encouragement.")
    para(doc, "", space_after=24)
    para(doc, f"{NAME}\n{ROLL}", align=WD_ALIGN_PARAGRAPH.RIGHT)


def abstract(doc, s):
    title_page_heading(doc, "ABSTRACT")
    para(doc, "Websites store a hash of each password rather than the password itself, but when "
              "a password database is leaked, an attacker can recover weak passwords offline by "
              "hashing guesses from a wordlist. This project, linked to Experiment 3 (Dictionary "
              "and Brute Force Attack) of the RTU Cyber Security Lab, builds a Python tool that "
              "measures how two defences change the cost of such an attack. Salting adds a "
              "random value to each password so identical passwords produce different hashes "
              "and precomputed tables become useless. Key stretching, using PBKDF2, bcrypt and "
              "Argon2id, makes every hash deliberately slow. The tool stores dummy passwords "
              "under six schemes, runs dictionary, brute-force and precomputed-table attacks "
              "against them, and benchmarks each scheme. On an Intel Core i5-1135G7, MD5 "
              f"computed about {s['MD5']['rate']:,.0f} hashes per second, while bcrypt (cost "
              f"12) computed about {s['bcrypt']['rate']:.1f}. Trying the 14.3 million-word "
              f"rockyou list against one hash would take {s['MD5']['crack']} with MD5 but "
              f"{s['bcrypt']['crack']} with bcrypt. A precomputed table cracked 5 of 6 "
              "unsalted hashes instantly and none of the salted ones. An interactive Streamlit "
              "application demonstrates these results live.")


def toc(doc):
    title_page_heading(doc, "TABLE OF CONTENTS")
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-2" \\h \\z \\u')


# ---------------------------------------------------------------- chapters

def ch1(doc):
    chapter(doc, 1, "Introduction")
    heading(doc, "1.1 Problem Statement", 2)
    para(doc, "Password databases are leaked regularly through SQL injection, misconfigured "
              "backups and insider access. If passwords are stored with a fast, unsalted hash "
              "such as MD5 or SHA-256, an attacker can test millions or billions of guesses per "
              "second offline, and identical passwords are visible as identical hashes. Many "
              "developers know that passwords should be “hashed” but do not know why "
              "the choice of hash function, the use of a salt and the work factor matter. This "
              "project demonstrates and measures these effects on real code.")
    heading(doc, "1.2 Objectives", 2)
    bullets(doc, [
        "Implement six password storage schemes behind one common interface: MD5, SHA-256, "
        "salted SHA-256, PBKDF2-HMAC-SHA256, bcrypt and Argon2id.",
        "Implement an offline dictionary attack and a brute-force attack against a simulated "
        "leaked database of dummy users.",
        "Demonstrate that a precomputed hash table cracks unsalted hashes instantly but fails "
        "completely against salted hashes.",
        "Benchmark each scheme and the effect of its cost parameter (iterations, cost factor, "
        "memory), and project the time to try a full 14.3 million-word wordlist.",
        "Provide an interactive web demo that shows all of the above live.",
    ])
    heading(doc, "1.3 Link to Syllabus Experiment", 2)
    para(doc, "Experiment 3 of the RTU Cyber Security Lab (7CS4-22) studies dictionary and "
              "brute-force attacks on passwords. That experiment shows how an attacker recovers "
              "passwords from hashes. This project extends it to the defender's side: it uses "
              "the same attacks, but measures how salting and key stretching change their cost. "
              "The attack code in this project is a direct implementation of the experiment, and "
              "the benchmark and salting demonstrations show why modern systems use bcrypt or "
              "Argon2 instead of plain hashes.")
    heading(doc, "1.4 Scope and Ethics", 2)
    para(doc, "All attacks run locally on one laptop against hashes generated by the project "
              "itself from dummy passwords (alice, bob, charlie, dave, eve and frank). No real "
              "accounts, passwords or external systems are involved, in line with the "
              "department's ethical rules and the Information Technology Act, 2000.")


def ch2(doc):
    chapter(doc, 2, "Background / Theory")
    heading(doc, "2.1 Cryptographic Hash Functions", 2)
    para(doc, "A cryptographic hash function maps any input to a fixed-length output. It is "
              "one-way (the input cannot be computed from the output), deterministic (the same "
              "input always gives the same output) and collision resistant. Systems store "
              "H(password) and, at login, compare H(entered password) with the stored value. "
              "General-purpose hashes such as MD5 and SHA-256 are designed to be fast, which is "
              "good for checking files but bad for passwords, because speed helps the attacker.")
    heading(doc, "2.2 Attacks on Stored Password Hashes", 2)
    bullets(doc, [
        ("Dictionary attack: ", "hash each word of a list of common passwords and compare it "
         "with the stolen hash. Effective because users choose predictable passwords."),
        ("Brute-force attack: ", "try every combination of characters up to some length. The "
         "search space is |charset|^length, e.g. 26^4 = 456,976 four-letter lowercase strings."),
        ("Precomputed table / rainbow table: ", "compute hash → password pairs once, before "
         "any leak, and crack each leaked hash with a single lookup. Rainbow tables store hash "
         "chains to trade lookup time for much less storage, but rely on the same idea."),
    ])
    heading(doc, "2.3 Salting", 2)
    para(doc, "A salt is a random value generated per password and stored next to the hash: "
              "stored = salt ‖ H(salt ‖ password). Salting has two effects. Identical "
              "passwords give different hashes, so the leak no longer reveals which users share "
              "a password. More importantly, a precomputed table would have to be built "
              "separately for every possible salt; with a 128-bit salt that is 2^128 tables, "
              "which is impossible. A salt does not make a single guess slower; it forces the "
              "attacker to attack each user separately.")
    heading(doc, "2.4 Key Stretching", 2)
    para(doc, "Key stretching makes each hash deliberately expensive. A legitimate user logs in "
              "once and does not notice a 0.3 second delay, but an attacker who must make "
              "millions of guesses pays that delay millions of times.")
    bullets(doc, [
        ("PBKDF2 (RFC 8018): ", "applies HMAC-SHA256 repeatedly. The cost grows linearly with "
         "the iteration count; OWASP currently recommends 600,000 iterations for SHA-256."),
        ("bcrypt: ", "based on the Blowfish key schedule. A cost factor c performs 2^c rounds, so "
         "each +1 doubles the work. The output string $2b$12$... stores the cost and 128-bit salt."),
        ("Argon2id (RFC 9106): ", "winner of the 2015 Password Hashing Competition. Besides a time "
         "cost it has a memory cost, so each guess needs, for example, 64 MiB of RAM. This makes "
         "GPU and ASIC attacks, which have many cores but little memory per core, far less "
         "effective."),
    ])
    heading(doc, "2.5 Constant-Time Comparison", 2)
    para(doc, "When verifying a hash, comparing strings with == can stop at the first different "
              "character, leaking timing information. The project uses hmac.compare_digest, "
              "which takes the same time regardless of where the strings differ.")


def ch3(doc):
    chapter(doc, 3, "Tools & Environment")
    table(doc, 3, "Hardware and software used", ["Item", "Details"], [
        ["Processor", "Intel Core i5-1135G7 @ 2.40 GHz (4 cores, 8 threads)"],
        ["RAM", "8 GB"],
        ["Operating System", "Windows 11 Home (build 26200)"],
        ["Language", "Python 3.14"],
        ["Hashing libraries", "hashlib (standard library), bcrypt 5.0, argon2-cffi 25.1"],
        ["Graphs", "Matplotlib 3.10"],
        ["Web demo", "Streamlit 1.66"],
        ["Screenshots", "Playwright with Microsoft Edge"],
        ["Editor / VCS", "Visual Studio Code, Git"],
    ], [4.5, 11])
    heading(doc, "3.1 Lab Setup", 2)
    para(doc, "No network or virtual machine is needed: the “server”, the leaked "
              "database and the attacker all run as Python code on the same laptop. The demo "
              "web server listens only on localhost:8501. Fig. 3.1 shows the flow.")
    fig_no[3] = 0
    figure(doc, 3, OUT_DIR / "assets" / "architecture.png",
           "System architecture and data flow", width_cm=15.5)
    heading(doc, "3.2 Project Structure", 2)
    table(doc, 3, "Source files", ["File", "Purpose"], [
        ["salting_demo/hashers.py", "Six hashing schemes with hash() and verify()"],
        ["salting_demo/attack.py", "Leaked database, dictionary and brute-force attacks"],
        ["salting_demo/rainbow.py", "Precomputed table attack vs salted hashes"],
        ["salting_demo/benchmark.py", "Timing, CSV results and graphs"],
        ["salting_demo/app.py", "Streamlit interactive demo"],
        ["data/users.json, wordlist.txt", "6 dummy users, 50-word test wordlist"],
        ["tools/*.py", "Screenshot and report generation"],
    ], [5.5, 10])
    para(doc, "Commands to reproduce: pip install -r requirements.txt, then "
              "python -m salting_demo.attack, python -m salting_demo.rainbow, "
              "python -m salting_demo.benchmark and streamlit run salting_demo/app.py.")


def ch4(doc):
    chapter(doc, 4, "Codes")
    para(doc, "This chapter lists the core logic. The complete source code, including the "
              "Streamlit interface and helper scripts, is in the submitted ZIP file.")
    heading(doc, "4.1 Hashing Schemes (hashers.py)", 2)
    code_block(doc, (ROOT / "salting_demo/hashers.py").read_text(encoding="utf-8"))
    heading(doc, "4.2 Attacks (attack.py)", 2)
    code_block(doc, source_of("salting_demo/attack.py",
                              {"build_leak", "dictionary_attack", "brute_force_candidates",
                               "brute_force_attack"}))
    heading(doc, "4.3 Precomputed Table Attack (rainbow.py)", 2)
    code_block(doc, source_of("salting_demo/rainbow.py", {"build_table", "lookup_attack"}))
    heading(doc, "4.4 Benchmark (benchmark.py)", 2)
    code_block(doc, source_of("salting_demo/benchmark.py", {"time_per_hash"}))


def ch5(doc, s):
    chapter(doc, 5, "Results & Testing")
    heading(doc, "5.1 Functional Test Cases", 2)
    table(doc, 5, "Functional test cases", ["#", "Test", "Expected", "Result"], [
        ["1", "verify() with correct password, all 6 schemes", "True", "Pass"],
        ["2", "verify() with wrong password, all 6 schemes", "False", "Pass"],
        ["3", "Hash same password twice, MD5/SHA-256", "Identical", "Pass"],
        ["4", "Hash same password twice, salted schemes", "Different", "Pass"],
        ["5", "Dictionary attack cracks weak users", "5/6 cracked", "Pass"],
        ["6", "Strong password (frank) not in wordlist", "Not cracked", "Pass"],
        ["7", "Precomputed table vs unsalted leak", "5/6 cracked", "Pass"],
        ["8", "Precomputed table vs salted leak", "0/6 cracked", "Pass"],
        ["9", "Brute force 'dog' (a-z, ≤3) on fast hashes", "Found", "Pass"],
        ["10", "Brute force 'dog' on slow hashes, 20 s limit", "Timeout", "Pass"],
    ], [1, 7.5, 3.5, 2.5])

    heading(doc, "5.2 Hashing: Salt Makes Each Hash Unique", 2)
    figure_pair(doc, 5, [
        (SHOTS / "ui_hash_md5.png", "MD5 produces the same hash twice"),
        (SHOTS / "ui_hash_salted.png", "Salted SHA-256 produces a different hash each time")])
    figure(doc, 5, SHOTS / "ui_hash_bcrypt.png",
           "bcrypt (cost 12): salted, and close to 1 s per hash", width_cm=11)

    heading(doc, "5.3 Dictionary and Brute-Force Attacks", 2)
    para(doc, "Fig. 5.4 shows the command-line attack on all six schemes with a 20 second "
              "limit. Every scheme gives up the same five weak passwords if the attacker waits "
              "long enough, because those words are in the wordlist; the difference is the "
              "time. The fast hashes finish in about a millisecond, whereas PBKDF2 and bcrypt "
              "hit the time limit after a few dozen guesses. Brute force finds “dog” "
              "in 0.01 s against fast hashes and times out against the slow ones.")
    figure(doc, 5, SHOTS / "cli_attack.png",
           "Dictionary and brute-force attack output for all schemes", width_cm=15)
    figure_pair(doc, 5, [
        (SHOTS / "ui_dict_md5.png", "Dictionary attack on MD5 in the web demo"),
        (SHOTS / "ui_dict_argon2.png", "Argon2id: attacker hits the 15 s limit after 59 guesses")])
    figure_pair(doc, 5, [
        (SHOTS / "ui_brute_sha256.png", "Brute force on SHA-256 finds the password"),
        (SHOTS / "ui_brute_bcrypt.png", "Brute force on bcrypt gives up after only 16 guesses")])

    heading(doc, "5.4 Precomputed Table vs Salt", 2)
    para(doc, "Without a salt, alice and dave, who both use “password”, have the same "
              "hash, and a 50-entry table built in advance cracks five of six users in "
              "microseconds. With a 16-byte random salt, their hashes differ and the same table "
              "cracks none (Fig. 5.9, Fig. 5.10).")
    figure(doc, 5, SHOTS / "cli_rainbow.png", "Precomputed table demonstration output",
           width_cm=15)
    figure(doc, 5, SHOTS / "ui_table_vs_salt.png", "Unsalted vs salted leak in the web demo")

    heading(doc, "5.5 Benchmark Results", 2)
    rows = [[r["scheme"], f"{float(r['ms_per_hash']):.4f}", f"{float(r['hashes_per_sec']):,.1f}",
             human_time(float(r["seconds_for_rockyou"]))] for r in read_csv("schemes.csv")]
    table(doc, 5, "Measured cost per scheme (single CPU core)",
          ["Scheme", "ms / hash", "Hashes / s", "14.3M words"], rows, [5.5, 2.8, 3.2, 3.5])
    figure(doc, 5, RESULTS / "schemes.png", "Guess rate per scheme (log scale)")
    figure(doc, 5, RESULTS / "crack_time.png",
           "Projected time to try the rockyou wordlist against one hash")

    heading(doc, "5.6 Effect of Cost Parameters", 2)
    pb, bc, ar = read_csv("pbkdf2_iterations.csv"), read_csv("bcrypt_cost.csv"), \
        read_csv("argon2_memory.csv")
    table(doc, 5, "PBKDF2 iterations vs time", ["Iterations", "ms / hash"],
          [[f"{int(r['iterations']):,}", f"{float(r['ms_per_hash']):.1f}"] for r in pb], [5, 5])
    table(doc, 5, "bcrypt cost vs time", ["Cost", "ms / hash"],
          [[r["cost"], f"{float(r['ms_per_hash']):.1f}"] for r in bc], [5, 5])
    table(doc, 5, "Argon2id memory vs time (t=3, p=4)", ["Memory (MiB)", "ms / hash"],
          [[r["memory_MiB"], f"{float(r['ms_per_hash']):.1f}"] for r in ar], [5, 5])
    figure_pair(doc, 5, [
        (RESULTS / "pbkdf2_iterations.png", "PBKDF2 time grows linearly with iterations"),
        (RESULTS / "bcrypt_cost.png", "bcrypt time roughly doubles per cost step")])
    figure(doc, 5, RESULTS / "argon2_memory.png", "Argon2id time grows with memory",
           width_cm=9)

    heading(doc, "5.7 Observations and Security Analysis", 2)
    ratio = s["MD5"]["rate"] / s["bcrypt"]["rate"]
    bullets(doc, [
        f"bcrypt (cost 12) is about {ratio:,.0f} times slower per guess than MD5 on this CPU. "
        f"The rockyou wordlist goes from {s['MD5']['crack']} to {s['bcrypt']['crack']} per hash.",
        "Salted SHA-256 is no slower per guess than unsalted SHA-256. Salt defeats precomputed "
        "tables and hides duplicate passwords but does not slow a dictionary attack on one user; "
        "it must be combined with key stretching.",
        "PBKDF2 scales linearly with iterations and bcrypt doubles per cost step, so defenders "
        "can raise the cost as hardware gets faster.",
        "Argon2id also needs memory per guess. A GPU with thousands of cores cannot give each "
        "core 64 MiB, which limits parallel cracking; PBKDF2 and bcrypt have no such limit.",
        "No scheme protects a password that is in the wordlist forever: slow hashing buys time, "
        "but strong, unique passwords (like frank's) are still required.",
        "These are single-core CPU numbers. A GPU makes MD5/SHA-256 billions of times per second, "
        "widening the gap further.",
    ])


def ch6(doc):
    chapter(doc, 6, "Conclusion & Future Scope")
    heading(doc, "6.1 Conclusion", 2)
    para(doc, "This project implemented and measured six password storage schemes against "
              "dictionary, brute-force and precomputed-table attacks. The results confirm the "
              "theory from Experiment 3 and modern guidance such as OWASP's: fast hashes like "
              "MD5 and SHA-256 let an attacker test a large wordlist in under a minute, salting "
              "removes the shortcut of precomputed tables and stops identical passwords from "
              "being visible, and key stretching with PBKDF2, bcrypt or Argon2id raises the cost "
              "of each guess by five orders of magnitude. Argon2id is the preferred choice "
              "because its memory cost also limits GPU attacks. The interactive demo makes "
              "these differences visible in a way that is easy to explain.")
    heading(doc, "6.2 Future Scope", 2)
    bullets(doc, [
        "Measure GPU cracking speed with Hashcat on the same hashes to show the gap more widely.",
        "Implement a true rainbow table with hash chains and reduction functions.",
        "Add a pepper (a server-side secret key) and show its effect if only the database leaks.",
        "Add an automatic tuning feature that picks parameters giving a target login time "
        "(for example 250 ms) on the current server.",
        "Add scrypt and compare it with Argon2id for memory hardness.",
    ])
    heading(doc, "References", 2)
    for ref in [
        "K. Moriarty, B. Kaliski, A. Rusch, “PKCS #5: Password-Based Cryptography "
        "Specification Version 2.1,” RFC 8018, IETF, 2017.",
        "A. Biryukov, D. Dinu, D. Khovratovich, S. Josefsson, “Argon2 Memory-Hard Function "
        "for Password Hashing and Proof-of-Work Applications,” RFC 9106, IETF, 2021.",
        "N. Provos, D. Mazières, “A Future-Adaptable Password Scheme,” USENIX "
        "Annual Technical Conference, 1999.",
        "P. Oechslin, “Making a Faster Cryptanalytic Time-Memory Trade-Off,” CRYPTO 2003.",
        "OWASP Foundation, “Password Storage Cheat Sheet,” cheatsheetseries.owasp.org.",
        "RTU Kota, Cyber Security Lab (7CS4-22) syllabus, Experiment 3.",
    ]:
        para(doc, ref, style="List Number", space_after=2)


# ---------------------------------------------------------------- architecture figure

def draw_architecture():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.2)
    ax.axis("off")

    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                    fc=color, ec="#1F3864", lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5,
                family="Times New Roman")

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", lw=1.2))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                    fontsize=9, family="Times New Roman", zorder=3,
                    bbox=dict(fc="white", ec="none", pad=1))

    box(0.1, 2.6, 1.9, 1.0, "users.json\n(6 dummy users)", "#E8EEF7")
    box(2.6, 2.6, 2.2, 1.0, "hashers.py\nMD5 · SHA-256 · salt\nPBKDF2 · bcrypt · Argon2", "#E8EEF7")
    box(5.4, 2.6, 1.9, 1.0, "Leaked database\n(user → stored hash)", "#FDECEA")
    box(7.9, 2.6, 2.0, 1.0, "attack.py\ndictionary / brute force", "#FDECEA")
    box(7.9, 0.4, 2.0, 1.0, "wordlist.txt\n(50 words)", "#E8EEF7")
    box(5.4, 0.4, 1.9, 1.0, "rainbow.py\nprecomputed table", "#FDECEA")
    box(2.6, 0.4, 2.2, 1.0, "benchmark.py\nCSV + graphs", "#E9F7EF")
    box(0.1, 0.4, 1.9, 1.0, "app.py (Streamlit)\nlocalhost:8501", "#E9F7EF")

    arrow(2.0, 3.1, 2.6, 3.1, "passwords")
    arrow(4.8, 3.1, 5.4, 3.1, "hash()")
    arrow(7.3, 3.1, 7.9, 3.1, "steal")
    arrow(8.9, 1.4, 8.9, 2.6, "guesses")
    arrow(7.9, 0.9, 7.3, 0.9, "words")
    arrow(6.35, 2.6, 6.35, 1.4, "lookup")
    arrow(3.7, 2.6, 3.7, 1.4, "timing")
    arrow(2.6, 0.9, 2.0, 0.9, "graphs")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "assets" / "architecture.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- main

def summary():
    s = {}
    for r in read_csv("schemes.csv"):
        key = r["scheme"].split(" ")[0] if not r["scheme"].startswith("SHA") else r["scheme"]
        s[key] = {"rate": float(r["hashes_per_sec"]),
                  "crack": human_time(float(r["seconds_for_rockyou"]))}
    return s


def export_pdf(docx_path, pdf_path):
    """Use Microsoft Word to update the TOC/page fields and save a PDF."""
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        d = word.Documents.Open(str(docx_path))
        d.Fields.Update()
        d.TablesOfContents(1).Update()
        d.Save()
        d.SaveAs2(str(pdf_path), FileFormat=17)  # 17 = PDF
        pages = d.ComputeStatistics(2)  # 2 = pages
        d.Close(False)
        return pages
    finally:
        word.Quit()


def main():
    OUT_DIR.mkdir(exist_ok=True)
    draw_architecture()
    s = summary()

    doc = Document()
    setup(doc)
    front_page(doc)
    declarations(doc)
    acknowledgement(doc)
    abstract(doc, s)
    toc(doc)
    ch1(doc)
    ch2(doc)
    ch3(doc)
    ch4(doc)
    ch5(doc, s)
    ch6(doc)

    docx_path = OUT_DIR / f"{BASENAME}.docx"
    doc.save(docx_path)
    pages = export_pdf(docx_path, OUT_DIR / f"{BASENAME}.pdf")
    print(f"Saved {docx_path.name} and PDF ({pages} pages)")


if __name__ == "__main__":
    main()
