#!/usr/bin/env python3
"""
skill_matcher.py – Find the best‑matching UW courses for any list of
skill phrases, letting the caller narrow results by subject, level, credit
amount, and “last taught” semester.

New flags
---------
--subject-contains TEXT   (case‑insensitive substring match)
--level-min N  --level-max N
--credit-min N --credit-max N
--last-taught F23 | S24 | U24   (“F”=Fall, “S”=Spring, “U”=Summer)

Examples
--------
python skill_matcher.py "data analysis" --subject-contains ACCT --level-min 100 --level-max 300
python skill_matcher.py "creative writing" --credit-max 3 --last-taught F23
"""

from __future__ import annotations

import argparse
import os
import re
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

load_dotenv()

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_ANON_PUBLIC_KEY: str = os.environ["SUPABASE_ANON_PUBLIC_KEY"]
TOP_K_SQL_DEFAULT: int = int(os.getenv("TOP_K", 5))
MODEL_NAME: str = "all-mpnet-base-v2"

# ---------------------------------------------------------------------
# Initialise external clients
# ---------------------------------------------------------------------

sb: Client = create_client(SUPABASE_URL, SUPABASE_ANON_PUBLIC_KEY)
model = SentenceTransformer(MODEL_NAME)

# ---------------------------------------------------------------------
# Helper parsers
# ---------------------------------------------------------------------

SEMESTER_ORDER: dict[str, int] = {"S": 0, "U": 1, "F": 2}
SEMESTER_RE = re.compile(r"^\s*([SUF])\s*([0-9]{2})\s*$", re.I)


def semester_code_to_int(code: str) -> int:
    """Convert a semester code like 'F24' to an integer that preserves
    chronological ordering when compared lexicographically.

    Example
    -------
    'F24' -> 2024 * 10 + 2
    'S25' -> 2025 * 10 + 0
    """
    m = SEMESTER_RE.fullmatch(code.upper())
    if not m:
        raise ValueError(
            f"Bad semester code: {code!r} (expected F23, S24, U24, …)"
        )
    season, yy = m.groups()
    return (2000 + int(yy)) * 10 + SEMESTER_ORDER[season]


def credit_range(raw: str) -> Tuple[float, float]:
    """Parse the ``credit_amount`` column into a (low, high) tuple."""
    parts = raw.replace("–", "-").split("-")
    try:
        if len(parts) == 1:
            val = float(parts[0])
            return val, val
        low, high = map(float, parts)
        return low, high
    except ValueError:
        # Malformed credit amount – treat as unbounded so filter never fails.
        return float("-inf"), float("inf")


# ---------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------

def get_skill_embeddings(skills: List[str]) -> List[list[float]]:
    """Return unit‑norm vectors for each skill string."""
    return model.encode(skills, normalize_embeddings=True).tolist()


def match(vector: list[float], k: int = TOP_K_SQL_DEFAULT):
    """Call the SQL helper *match_courses* and return the rows."""
    resp = sb.rpc("match_courses", {"skill": vector, "k": k}).execute()
    return resp.data or []


# ---------------------------------------------------------------------
# Filter logic
# ---------------------------------------------------------------------

def course_passes_filters(
    row: dict,
    *,
    subj_contains: Optional[str] = None,
    lvl_min: Optional[int] = None,
    lvl_max: Optional[int] = None,
    cr_min: Optional[float] = None,
    cr_max: Optional[float] = None,
    last_taught_int: Optional[int] = None,
) -> bool:
    """Return ``True`` iff *all* supplied filters match *row*."""
    # Subject
    if subj_contains and subj_contains.lower() not in row["subject"].lower():
        return False

    # Level
    if lvl_min is not None and row["level"] < lvl_min:
        return False
    if lvl_max is not None and row["level"] > lvl_max:
        return False

    # Credit amount – handle ranges in the DB like '1‑6'
    low, high = credit_range(str(row["credit_amount"]))
    if cr_min is not None and high < cr_min:
        return False
    if cr_max is not None and low > cr_max:
        return False

    # Last taught – treat missing/null as very old (filter them out)
    if last_taught_int is not None:
        try:
            course_sem_int = semester_code_to_int(str(row["last_taught"]))
        except ValueError:
            return False
        if course_sem_int < last_taught_int:
            return False

    return True


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find the best‑matching UW courses for a list of skills."
        )
    )
    parser.add_argument(
        "skills", nargs="+", help="Skill phrases, e.g. 'data analysis'"
    )
    parser.add_argument("--subject-contains")
    parser.add_argument("--level-min", type=int)
    parser.add_argument("--level-max", type=int)
    parser.add_argument("--credit-min", type=float)
    parser.add_argument("--credit-max", type=float)
    parser.add_argument(
        "--last-taught",
        help=(
            "Semester code like F23, S24, U24. "
            "Courses taught *on or after* this semester are kept."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    last_taught_int = (
        semester_code_to_int(args.last_taught) if args.last_taught else None
    )
    vectors = get_skill_embeddings(args.skills)

    for skill, vec in zip(args.skills, vectors):
        print(
            f"\n🔍 Best courses for “{skill}” "
            f"(Top {TOP_K_SQL_DEFAULT} Courses)"
        )
        rows = match(vec, k=TOP_K_SQL_DEFAULT)
        filtered = [
            r
            for r in rows
            if course_passes_filters(
                r,
                subj_contains=args.subject_contains,
                lvl_min=args.level_min,
                lvl_max=args.level_max,
                cr_min=args.credit_min,
                cr_max=args.credit_max,
                last_taught_int=last_taught_int,
            )
        ]

        if not filtered:
            print("⟡  None matched your filters.")
            continue

        for r in filtered:
            print(
                f"{r['subject']} {r['level']} - {r['title']} "
                f"(Credit Amount: {r['credit_amount']}, "
                f"Last Taught: {r['last_taught']}) | "
                f"{r['similarity']:.3f}"
            )


if __name__ == "__main__":
    main()
