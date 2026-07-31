import json
import re
from threading import Lock
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

QUESTION_START = re.compile(r"(?m)^\s*(\d{1,3})(?:[.)]\s*|\s+)(?=\S)")
ANSWER_SECTION = re.compile(
    r"(?m)^\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ /-]{2,})\s*$"
)
PDF_RENDER_LOCK = Lock()
OPTION_START = re.compile(r"(?m)^\s*[\(\[]?([A-Ea-e])[\)\].\-]\s+")
ANSWER_PAIR = re.compile(r"(?<!\d)(\d{1,3})\s*[-–—:]\s*([A-Ea-e])\b")
def extract_best_text(page) -> str:
    """Use plain extraction when positioned text loses most of the content."""
    layout_text = page.extract_text(extraction_mode="layout") or ""
    plain_text = page.extract_text() or ""
    layout_signal = sum(character.isalnum() for character in layout_text)
    plain_signal = sum(character.isalnum() for character in plain_text)
    return plain_text if plain_signal > layout_signal * 1.35 else layout_text


def extract_pdf_preview(pdf_path: Path, output_dir: Path, document_type: str = "exam") -> dict:
    reader = PdfReader(str(pdf_path))
    pages: list[dict] = []
    full_text: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = extract_best_text(page)
        pages.append({"page": page_number, "characters": len(text)})
        full_text.append(f"\n--- PAGE {page_number} ---\n{text}")
    joined = "\n".join(full_text)
    candidates = detect_candidates(joined) if document_type == "exam" else []
    if candidates:
        render_question_crops(pdf_path, output_dir, candidates)
    answers = detect_answer_key(joined) if document_type == "answer_key" else {}

    output_dir.mkdir(parents=True, exist_ok=True)
    text_path = output_dir / "extracted.txt"
    preview_path = output_dir / "preview.json"
    text_path.write_text(joined, encoding="utf-8")
    preview = {
        "page_count": len(reader.pages),
        "pages": pages,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "answer_count": len(answers),
        "answers": answers,
        "warnings": [
            "Prévia automática: confirme numeração, alternativas e gabarito antes de importar.",
            "Nenhuma questão foi publicada por esta inspeção.",
        ],
    }
    preview_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        **preview,
        "text_path": str(text_path),
        "preview_path": str(preview_path),
    }


def detect_candidates(text: str) -> list[dict]:
    normalized_lines = []
    embedded_question = re.compile(r"(?<!\d)(\d{1,3}\.)\s{2,}(?=[A-ZÁÉÍÓÚ])")
    for line in text.splitlines():
        match = embedded_question.search(line)
        if match and line[:match.start()].strip():
            line = line[match.start():]
        normalized_lines.append(line)
    text = "\n".join(normalized_lines)
    starts = list(QUESTION_START.finditer(text))
    candidates: list[dict] = []
    for index, match in enumerate(starts):
        if int(match.group(1)) > 150:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.end():end].strip()
        if len(block) < 30:
            continue
        option_matches = list(OPTION_START.finditer(block))
        if len(option_matches) < 2:
            continue
        statement = block[:option_matches[0].start()].strip()
        options = []
        for option_index, option_match in enumerate(option_matches):
            option_end = option_matches[option_index + 1].start() if option_index + 1 < len(option_matches) else len(block)
            options.append(re.sub(r"\s+", " ", block[option_match.end():option_end].strip()))
        candidates.append({
            "number": int(match.group(1)),
            "statement": re.sub(r"\s+", " ", statement),
            "options": options,
            "page_number": page_number_at(text, match.start()),
            "confidence": "high" if len(options) in {4, 5} and len(statement) >= 20 else "review",
        })
    strongest: dict[int, dict] = {}
    for candidate in candidates:
        current = strongest.get(candidate["number"])
        score = (
            int(len(candidate["options"]) in {4, 5}),
            int(candidate["confidence"] == "high"),
            len(candidate["statement"]),
        )
        current_score = (
            int(len(current["options"]) in {4, 5}),
            int(current["confidence"] == "high"),
            len(current["statement"]),
        ) if current else (-1, -1, -1)
        if score > current_score:
            strongest[candidate["number"]] = candidate
    return [strongest[number] for number in sorted(strongest)]


def page_number_at(text: str, position: int) -> int | None:
    markers = list(re.finditer(r"--- PAGE (\d+) ---", text[:position]))
    return int(markers[-1].group(1)) if markers else None


def render_question_crops(pdf_path: Path, output_dir: Path, candidates: list[dict]) -> None:
    """Render a visual reference for every detected question.

    The crop preserves diagrams, tables and formatting that text extraction loses.
    """
    image_dir = output_dir / "question-images"
    image_dir.mkdir(parents=True, exist_ok=True)
    by_page: dict[int, list[dict]] = {}
    for candidate in candidates:
        if candidate.get("page_number"):
            by_page.setdefault(candidate["page_number"], []).append(candidate)

    with PDF_RENDER_LOCK, pdfplumber.open(str(pdf_path)) as document:
        for page_number, page_candidates in by_page.items():
            if page_number < 1 or page_number > len(document.pages):
                continue
            page = document.pages[page_number - 1]
            words = page.extract_words(keep_blank_chars=False)
            positions: dict[int, list[float]] = {}
            for word in words:
                match = re.fullmatch(r"(\d{1,3})[.)]?", word.get("text", ""))
                if match:
                    positions.setdefault(int(match.group(1)), []).append(float(word["top"]))
            starts = {
                number: next((top for top in tops if top > 50), tops[0])
                for number, tops in positions.items()
            }
            ordered_tops = sorted(set(starts.values()))
            for candidate in page_candidates:
                top = starts.get(candidate["number"])
                if top is None:
                    continue
                following = [value for value in ordered_tops if value > top + 2]
                bottom = min(following) - 4 if following else float(page.height) - 10
                if bottom <= top + 20:
                    continue
                crop = page.crop((0, max(0, top - 8), float(page.width), bottom))
                filename = f"question-{candidate['number']:03d}.png"
                crop.to_image(resolution=130, antialias=True).save(
                    image_dir / filename, format="PNG"
                )
                candidate["image_file"] = filename


def detect_answer_key(text: str) -> dict[str, int]:
    sections = list(ANSWER_SECTION.finditer(text))
    candidates: list[dict[str, int]] = []
    for index, section in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        answers = {
            number: ord(letter.upper()) - ord("A")
            for number, letter in ANSWER_PAIR.findall(text[section.end():end])
        }
        if answers:
            candidates.append(answers)
    if candidates:
        return max(candidates, key=len)
    return {
        number: ord(letter.upper()) - ord("A")
        for number, letter in ANSWER_PAIR.findall(text)
    }
