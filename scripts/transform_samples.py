#!/usr/bin/env python3
"""Transform PDFs in data/samples per Micha spec.

Rules:
- In every PDF, replace articles, verbs, adjectives with '*', leaving only nouns.
  Practical heuristic (German-focused): keep capitalized words (incl. ALLCAPS) as nouns,
  mask everything else that is alphabetic.
  Additionally, always mask common articles even if capitalized (e.g., at line start).
- Increment all numbers in running text by +4, BUT on title page (page 1) numbers are untouched.
- For exactly 8 PDFs, append a dish synonym to the thick (largest-font) title line on title page.
  4 dish terms, 2 PDFs each.

Implementation notes:
- Uses pdfplumber to extract text + per-char font sizes.
- Rebuilds PDFs with reportlab, preserving page size and line breaks (layout not identical).
- Creates a timestamped backup directory alongside samples.
"""

from __future__ import annotations

import os
import re
import shutil
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "data" / "samples"

# Articles & determiners to always mask.
ARTICLES = {
    # German definite/indefinite
    "der", "die", "das", "des", "dem", "den",
    "ein", "eine", "einer", "eines", "einem", "einen",
    "kein", "keine", "keiner", "keines", "keinem", "keinen",
    # contractions/common
    "im", "ins", "am", "ans", "beim", "zum", "zur", "vom",
    # English articles (just in case)
    "a", "an", "the",
}

WORD_RE = re.compile(r"\b[\wÄÖÜäöüß]+\b", re.UNICODE)
NUM_RE = re.compile(r"\d+")


def is_probable_noun(word: str) -> bool:
    """Heuristic noun detector.

    Keep capitalized words (German noun convention) and ALLCAPS.
    Mask everything else.
    """
    if not word:
        return False
    w = word
    wl = w.lower()
    if wl in ARTICLES:
        return False

    # Keep roman numerals as nouns-ish tokens.
    if re.fullmatch(r"[IVXLCDM]+", w):
        return True

    # Keep ALLCAPS tokens (acronyms)
    letters = re.sub(r"[^A-Za-zÄÖÜäöüß]", "", w)
    if letters and letters.isupper():
        return True

    # Keep if starts with uppercase (including umlauts)
    first = w[0]
    if first.isalpha() and first == first.upper():
        return True

    return False


def mask_words_keep_nouns(text: str) -> str:
    def repl(m: re.Match) -> str:
        w = m.group(0)
        return w if is_probable_noun(w) else "*"

    return WORD_RE.sub(repl, text)


def increment_numbers(text: str) -> str:
    def repl(m: re.Match) -> str:
        n = int(m.group(0))
        return str(n + 4)

    return NUM_RE.sub(repl, text)


@dataclass
class TitleLineInfo:
    line_text: str
    # y position used for grouping (top-down coordinate system within pdfplumber)
    y_key: float


def find_thick_title_line(page) -> Optional[TitleLineInfo]:
    """Find the line with the largest average font size on a pdfplumber page."""
    chars = page.chars or []
    if not chars:
        return None

    # Group chars by rounded 'top' to form lines.
    buckets: dict[float, list[dict]] = {}
    for ch in chars:
        top = float(ch.get("top", 0.0))
        key = round(top, 1)  # 0.1 pt bucket
        buckets.setdefault(key, []).append(ch)

    best_key = None
    best_score = -1.0
    best_text = None

    for key, items in buckets.items():
        # compute average font size weighted by char count
        sizes = [float(it.get("size", 0.0)) for it in items]
        if not sizes:
            continue
        avg_size = sum(sizes) / len(sizes)

        # Build text in reading order by x0
        items_sorted = sorted(items, key=lambda it: float(it.get("x0", 0.0)))
        txt = "".join(it.get("text", "") for it in items_sorted).strip()
        if not txt:
            continue

        # Prefer longer lines a bit to avoid picking a giant single letter.
        score = avg_size * (1.0 + min(len(txt), 80) / 200.0)
        if score > best_score:
            best_score = score
            best_key = key
            best_text = txt

    if best_key is None or not best_text:
        return None

    return TitleLineInfo(line_text=best_text, y_key=float(best_key))


def wrap_line(line: str, max_chars: int) -> list[str]:
    if len(line) <= max_chars:
        return [line]
    out: list[str] = []
    cur = ""
    for part in re.split(r"(\s+)", line):
        if not part:
            continue
        if len(cur) + len(part) <= max_chars:
            cur += part
        else:
            if cur:
                out.append(cur.rstrip())
            # If a single token is huge, hard split
            if len(part) > max_chars:
                for i in range(0, len(part), max_chars):
                    out.append(part[i : i + max_chars])
                cur = ""
            else:
                cur = part.lstrip()
    if cur:
        out.append(cur.rstrip())
    return out


def rebuild_pdf(
    src_pdf: Path,
    dst_pdf: Path,
    dish_append: Optional[str],
) -> None:
    with pdfplumber.open(str(src_pdf)) as pdf:
        if not pdf.pages:
            raise ValueError(f"No pages in {src_pdf}")

        first_page = pdf.pages[0]
        title_info = find_thick_title_line(first_page)
        # Extract text pages first
        page_texts: list[str] = []
        for i, p in enumerate(pdf.pages):
            txt = p.extract_text() or ""
            # Normalize line endings
            txt = txt.replace("\r\n", "\n").replace("\r", "\n")
            if i == 0 and dish_append and title_info and title_info.line_text:
                # Replace first occurrence of detected title line with appended dish.
                # Be conservative: exact match replacement on a line basis.
                lines = txt.split("\n")
                replaced = False
                for li, line in enumerate(lines):
                    if not replaced and line.strip() == title_info.line_text.strip():
                        lines[li] = line.rstrip() + f" {dish_append}"
                        replaced = True
                if not replaced:
                    # Fallback: append to first non-empty line
                    for li, line in enumerate(lines):
                        if line.strip():
                            lines[li] = line.rstrip() + f" {dish_append}"
                            break
                txt = "\n".join(lines)
            page_texts.append(txt)

        # Transform text according to rules
        transformed: list[str] = []
        for i, txt in enumerate(page_texts):
            # Mask words, keep nouns
            t = mask_words_keep_nouns(txt)
            # Increment numbers except title page (page 1)
            if i != 0:
                t = increment_numbers(t)
            transformed.append(t)

        # Render new PDF
        dst_pdf.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(dst_pdf))
        # Use a font that supports umlauts; Helvetica generally does.
        font_name = "Helvetica"
        font_size = 10
        c.setFont(font_name, font_size)

        for i, p in enumerate(pdf.pages):
            w = float(p.width)
            h = float(p.height)
            c.setPageSize((w, h))

            margin_x = 36
            margin_y = 36
            line_height = 12
            max_width_pts = w - 2 * margin_x
            # crude chars-per-line estimate for wrapping
            avg_char_width = 5.5  # pts, rough for Helvetica 10
            max_chars = max(20, int(max_width_pts / avg_char_width))

            y = h - margin_y
            for raw_line in transformed[i].split("\n"):
                for line in wrap_line(raw_line, max_chars):
                    y -= line_height
                    if y < margin_y:
                        c.showPage()
                        c.setPageSize((w, h))
                        c.setFont(font_name, font_size)
                        y = h - margin_y - line_height
                    c.drawString(margin_x, y, line)
            c.showPage()

        c.save()


def main() -> None:
    if not SAMPLES_DIR.exists():
        raise SystemExit(f"Samples dir not found: {SAMPLES_DIR}")

    pdfs = sorted([p for p in SAMPLES_DIR.glob("*.pdf") if p.is_file()])
    if len(pdfs) != 25:
        print(f"Warning: expected 25 PDFs, found {len(pdfs)}")

    # Pick 8 random PDFs for title dish appends
    rnd = random.Random(42)  # deterministic surprise
    picked = rnd.sample(pdfs, k=min(8, len(pdfs)))

    dish_terms = ["(Gratin)", "(Auflauf)", "(Überbackenes)", "(Ofengericht)"]
    # 2 PDFs per term
    dish_assign: dict[Path, str] = {}
    for term_i, term in enumerate(dish_terms):
        for p in picked[term_i * 2 : term_i * 2 + 2]:
            dish_assign[p] = term

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = SAMPLES_DIR.parent / f"samples_backup_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup originals
    for p in pdfs:
        shutil.copy2(p, backup_dir / p.name)

    # Transform in-place via temp
    tmp_dir = SAMPLES_DIR.parent / f"samples_tmp_{stamp}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for p in pdfs:
        dish = dish_assign.get(p)
        dst = tmp_dir / p.name
        rebuild_pdf(p, dst, dish)

    # Replace originals
    for p in pdfs:
        shutil.move(str(tmp_dir / p.name), str(p))

    # Cleanup tmp dir
    try:
        tmp_dir.rmdir()
    except OSError:
        pass

    # Print assignment summary
    print("Dish title append assignments (8 PDFs):")
    for p in picked:
        print(f"- {p.name}: {dish_assign.get(p, '(none)')}")
    print(f"Backups: {backup_dir}")


if __name__ == "__main__":
    main()
