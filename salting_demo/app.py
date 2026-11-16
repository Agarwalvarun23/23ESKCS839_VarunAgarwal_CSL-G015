"""Interactive demo for CSL-G15: Salting & Key Stretching Demonstrator.

Run from the project root:
    streamlit run salting_demo/app.py
"""

import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so "salting_demo" imports work under streamlit

from salting_demo.attack import (brute_force_attack, build_leak,  # noqa: E402
                                 dictionary_attack, load_users, load_wordlist)
from salting_demo.benchmark import ROCKYOU_WORDS, human_time  # noqa: E402
from salting_demo.hashers import (Argon2Hasher, BcryptHasher,  # noqa: E402
                                  MD5Hasher, PBKDF2Hasher, SaltedSHA256Hasher,
                                  SHA256Hasher)
from salting_demo.rainbow import build_table, lookup_attack  # noqa: E402

st.set_page_config(page_title="Salting & Key Stretching", page_icon="🔐", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 2.2rem; max-width: 1150px;}
  h1 {font-weight: 750; letter-spacing: -0.02em;}
  .lead {font-size: 1.08rem; color: #4a5060; max-width: 760px; line-height: 1.6;}
  .card {background: #ffffff; border: 1px solid #e6e1d6; border-radius: 14px;
         padding: 1rem 1.2rem; margin: 0.4rem 0 1rem;}
  .card b {color: #1f2430;}
  .pill {display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
         font-size: 0.85rem; font-weight: 600;}
  .weak {background: #fde8e6; color: #a8261b;}
  .ok {background: #fff3d6; color: #8a5a00;}
  .strong {background: #e3f4e8; color: #1d6b38;}
  [data-testid=stMetric] {background: #ffffff; border: 1px solid #e6e1d6;
                          border-radius: 12px; padding: 0.8rem 1rem;}
  .stTabs [data-baseweb=tab] {font-size: 1rem; padding: 0.6rem 0.9rem;}
</style>
""", unsafe_allow_html=True)

# Plain-language description of each scheme, shown in the sidebar.
SCHEMES = {
    "MD5": ("weak", "Fast and unsalted. Built for checksums, not passwords."),
    "SHA-256": ("weak", "Modern, but still fast and unsalted. Same problem as MD5."),
    "SHA-256 + salt": ("ok", "Random salt per user. Stops lookup tables, but each guess is still fast."),
    "PBKDF2": ("strong", "Salted, and repeats the hash many times to make each guess slow."),
    "bcrypt": ("strong", "Salted and deliberately slow. Each +1 in cost doubles the work."),
    "Argon2id": ("strong", "Salted, slow and needs lots of memory, which makes GPU cracking expensive."),
}
VERDICT = {"weak": "Easy to crack", "ok": "Better", "strong": "Hard to crack"}


def make_hasher(scheme, pbkdf2_iters, bcrypt_cost, argon_mib):
    return {
        "MD5": lambda: MD5Hasher(),
        "SHA-256": lambda: SHA256Hasher(),
        "SHA-256 + salt": lambda: SaltedSHA256Hasher(),
        "PBKDF2": lambda: PBKDF2Hasher(pbkdf2_iters),
        "bcrypt": lambda: BcryptHasher(bcrypt_cost),
        "Argon2id": lambda: Argon2Hasher(memory_kib=argon_mib * 1024),
    }[scheme]()


def card(html):
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def pill(level):
    return f'<span class="pill {level}">{VERDICT[level]}</span>'


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### How are passwords stored?")
    scheme = st.radio("Hashing scheme", list(SCHEMES), label_visibility="collapsed")
    level, blurb = SCHEMES[scheme]
    st.markdown(f"{pill(level)}<br><span style='color:#4a5060'>{blurb}</span>",
                unsafe_allow_html=True)

    with st.expander("Advanced settings"):
        pbkdf2_iters = st.select_slider("PBKDF2 iterations",
                                        [1_000, 10_000, 100_000, 300_000, 600_000],
                                        value=600_000)
        bcrypt_cost = st.slider("bcrypt cost", 4, 14, 12)
        argon_mib = st.select_slider("Argon2 memory (MiB)", [8, 16, 32, 64, 128], value=64)
    time_limit = st.slider("Give the attacker this many seconds", 5, 60, 15)

    st.divider()
    st.caption("CSL-G15 · Varun Agarwal (23ESKCS839)  \n"
               "All passwords here are made up. Nothing leaves this computer.")

hasher = make_hasher(scheme, pbkdf2_iters, bcrypt_cost, argon_mib)

# ---------- Header ----------
st.title("🔐 How safe is a stolen password?")
st.markdown(
    '<p class="lead">Imagine a website gets hacked and its password database leaks. '
    "The passwords aren't stored in plain text, only as hashes, so the attacker has to "
    "guess. This demo shows how much the <b>choice of hashing</b> changes how long that "
    "guessing takes. Pick a scheme on the left and try each step below.</p>",
    unsafe_allow_html=True)

tab_hash, tab_dict, tab_brute, tab_table, tab_bench = st.tabs(
    ["🔑 Hash a password", "📖 Dictionary attack", "🔨 Brute force",
     "🧂 Why salt matters", "📊 The big picture"])

# ---------- 1. Hash a password ----------
with tab_hash:
    st.subheader(f"What does {hasher.name} turn a password into?")
    st.write("Type a password and hash it twice. Watch whether the two results match, "
             "and how long one hash takes. That time is what an attacker pays for every guess.")
    pw = st.text_input("Try a password", "sunshine")
    if st.button("Hash it twice", type="primary"):
        h1 = hasher.hash(pw)
        h2 = hasher.hash(pw)
        # Average over many runs; a single fast hash is too quick to time reliably.
        runs, t0 = 0, time.perf_counter()
        while time.perf_counter() - t0 < 0.3 or runs < 1:
            hasher.hash(pw)
            runs += 1
        secs = (time.perf_counter() - t0) / runs

        st.caption("First hash")
        st.code(h1, language=None)
        st.caption("Second hash of the same password")
        st.code(h2, language=None)

        c1, c2, c3 = st.columns(3)
        c1.metric("Time for one hash", f"{secs * 1000:.3f} ms")
        c2.metric("Guesses an attacker can make per second", f"{1 / secs:,.0f}")
        c3.metric("Same result both times?", "Yes" if h1 == h2 else "No")

        same = ("<b>Both hashes are identical.</b> Anyone who sees the database can tell "
                "which users share a password, and a table prepared in advance can crack it "
                "instantly." if h1 == h2 else
                "<b>The hashes are different</b> because a fresh random salt was mixed in "
                "each time. Two users with the same password won't look alike.")
        card(f"{same}<br><br>At this speed, trying the {ROCKYOU_WORDS:,} most common "
             f"leaked passwords would take about <b>{human_time(secs * ROCKYOU_WORDS)}</b> "
             "on this one laptop core.")
        st.caption(f"Check: correct password verifies → {hasher.verify(pw, h1)}, "
                   f"wrong password verifies → {hasher.verify(pw + 'x', h1)}")

# ---------- 2. Dictionary attack ----------
with tab_dict:
    users, wordlist = load_users(), load_wordlist()
    st.subheader("Can the attacker guess everyone's password?")
    st.write(f"We store {len(users)} made-up users with **{hasher.name}**, pretend the "
             f"database leaked, and try a list of {len(wordlist)} common passwords against "
             "each user.")
    if st.button("Start the attack", type="primary"):
        with st.spinner("Storing the users' passwords..."):
            leak = build_leak(hasher, users)
        with st.spinner("Attacker is guessing..."):
            cracked, guesses, secs, done = dictionary_attack(hasher, leak, wordlist, time_limit)

        c1, c2, c3 = st.columns(3)
        c1.metric("Passwords cracked", f"{len(cracked)} of {len(users)}")
        c2.metric("Guesses made", guesses)
        c3.metric("Time taken", f"{secs:.3f} s")

        st.dataframe(
            [{"User": u, "Result": f"Cracked: {cracked[u]}" if u in cracked else "Still safe",
              "What the attacker stole": h[:60] + ("…" if len(h) > 60 else "")}
             for u, h in leak.items()],
            width="stretch", hide_index=True)

        if not done:
            card(f"⏱️ The attacker ran out of time after <b>{time_limit} s</b>, having made "
                 f"only {guesses} guesses. Slow hashing is doing its job: with a real "
                 "wordlist of millions of words, this would take weeks.")
        elif secs < 1:
            card(f"⚡ Every guess was so cheap that the whole attack took "
                 f"<b>{secs * 1000:.1f} ms</b>. Weak passwords fall instantly with a fast hash.")
        if done and "frank" not in cracked:
            st.caption("Frank survives because his password isn't in the wordlist. "
                       "A strong, unusual password still matters.")

# ---------- 3. Brute force ----------
with tab_brute:
    st.subheader("What if the attacker just tries every combination?")
    st.write("Brute force doesn't need a wordlist: it tries a, b, c, … aa, ab, … until it "
             "hits the right one. Short passwords have surprisingly few combinations.")
    c1, c2 = st.columns(2)
    target = c1.text_input("Short password to crack (lowercase, up to 4 letters)", "dog",
                           max_chars=4)
    max_len = c2.slider("Try lengths up to", 1, 4, 3)
    space = sum(26 ** i for i in range(1, max_len + 1))
    st.caption(f"That's {space:,} possible passwords to try.")
    if st.button("Start brute force", type="primary"):
        with st.spinner("Trying every combination..."):
            found, guesses, secs, done = brute_force_attack(
                hasher, hasher.hash(target), max_len, time_limit)
        c1, c2, c3 = st.columns(3)
        c1.metric("Found it?", found or ("Not in range" if done else "Gave up"))
        c2.metric("Combinations tried", f"{guesses:,} of {space:,}")
        c3.metric("Time taken", f"{secs:.3f} s")
        if found:
            card(f"🔓 Cracked <b>“{found}”</b> in {secs:.3f} s. When guesses are this "
                 "cheap, short passwords offer almost no protection.")
        elif done:
            card("🤔 The attacker tried every combination and didn't find it. The password "
                 "is outside the search: it uses characters other than a–z, or it's longer "
                 "than the lengths being tried. A bigger character set or a longer password "
                 "makes brute force far harder.")
        else:
            rate = guesses / secs if secs else 0
            full = space / rate if rate else 0
            card(f"🔒 After {secs:.0f} s the attacker had tried only {guesses:,} "
                 f"combinations. Covering all {space:,} would take about "
                 f"<b>{human_time(full)}</b> for this one password.")

# ---------- 4. Why salt matters ----------
with tab_table:
    st.subheader("Why does a random salt help?")
    st.write("Attackers can prepare ahead of time: hash a list of common passwords once, "
             "then crack any leaked hash with a single lookup. Here we try that shortcut "
             "on two copies of the same database: one plain SHA-256, one salted.")
    if st.button("Try the lookup table", type="primary"):
        users, wordlist = load_users(), load_wordlist()
        sha, salted = SHA256Hasher(), SaltedSHA256Hasher()
        table = build_table(sha, wordlist)
        plain_leak = build_leak(sha, users)
        salted_leak = build_leak(salted, users)
        plain_cracked = lookup_attack(table, plain_leak)
        salted_cracked = lookup_attack(table, {u: h.split("$")[1] for u, h in salted_leak.items()})

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Without salt")
            st.dataframe([{"User": u, "Stored hash": h[:22] + "…"} for u, h in plain_leak.items()],
                         width="stretch", hide_index=True)
            st.error(f"Lookup cracked **{len(plain_cracked)} of {len(users)}** instantly: "
                     + ", ".join(f"{u} ({p})" for u, p in plain_cracked.items()))
        with c2:
            st.markdown("#### With salt")
            st.dataframe([{"User": u, "Salt $ hash": h[:22] + "…"} for u, h in salted_leak.items()],
                         width="stretch", hide_index=True)
            st.success(f"Lookup cracked **{len(salted_cracked)} of {len(users)}**.")

        same_plain = plain_leak["alice"] == plain_leak["dave"]
        same_salted = salted_leak["alice"] == salted_leak["dave"]
        card("👀 Alice and Dave both chose “password”. "
             f"Without salt their hashes are {'<b>identical</b>' if same_plain else 'different'}, "
             "so the leak gives them away. "
             f"With salt they are {'identical' if same_salted else '<b>completely different</b>'}, "
             "and the prepared table is useless. The attacker has to start from scratch "
             "for every single user.")

# ---------- 5. The big picture ----------
with tab_bench:
    st.subheader("Putting it all together")
    st.write("These numbers were measured on this laptop by `python -m salting_demo.benchmark`. "
             "The scale is logarithmic: each step up is 10× more.")
    results = ROOT / "results"
    missing = [n for n in ("crack_time.png", "schemes.png") if not (results / n).exists()]
    if missing:
        st.info("Run `python -m salting_demo.benchmark` first to create the graphs.")
    else:
        st.image(str(results / "crack_time.png"),
                 caption="How long one core needs to try every rockyou password against one hash")
        card("📌 <b>The takeaway:</b> fast hashes like MD5 fall in under a minute. Salt alone "
             "doesn't slow a single guess down. PBKDF2, bcrypt and Argon2 turn the same attack "
             "into weeks or months, and Argon2 also needs memory, which slows GPUs down.")
        with st.expander("More graphs: how each setting changes the cost"):
            st.image(str(results / "schemes.png"), caption="Guesses per second for each scheme")
            g1, g2, g3 = st.columns(3)
            for col, (name, caption) in zip((g1, g2, g3), [
                    ("pbkdf2_iterations.png", "PBKDF2: more iterations, more time"),
                    ("bcrypt_cost.png", "bcrypt: +1 cost doubles the time"),
                    ("argon2_memory.png", "Argon2: more memory, more time")]):
                if (results / name).exists():
                    col.image(str(results / name), caption=caption)
