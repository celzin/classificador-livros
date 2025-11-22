import os
import requests
import re
import unidecode
from typing import Dict, Optional, List

# =========================
# CONFIG
# =========================
GUTENDEX_BASE = "https://gutendex.com/books"
TIMEOUT = 10000
BOOKS_TO_DOWNLOAD = 150   # total de livros difíceis que queremos baixar

# Diretório onde vamos salvar os livros difíceis
SAVE_DIR = "books/hard_genres"

# Lista de categorias difíceis
HARD_GENRES = [
    "poetry",
    "religion",
    "bible",
    "sermons",
    "philosophy",
    "metaphysics",
    "ethics",
    "logic",
    "theology",
    "ancient",
    "classical",
    "science",
    "astronomy",
    "geometry",
    "mathematics"
]

# =========================
# GUTENDEX HELPERS
# =========================
def pick_best_text_url(formats: Dict[str, str]) -> Optional[str]:
    candidates = [
        "text/plain; charset=utf-8",
        "text/plain; charset=us-ascii",
        "text/plain",
    ]
    for key in candidates:
        if key in formats:
            return formats[key]

    for k, v in formats.items():
        if k.startswith("text/plain"):
            return v

    return None


def download_text(url: str) -> str:
    r = requests.get(url, timeout=TIMEOUT)
    if not r.encoding:
        r.encoding = "utf-8"
    return r.text


def strip_gutenberg_boilerplate(raw_text: str) -> str:
    _START_RE = re.compile(
        r"\*\*\*\s*START OF (?:THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*",
        re.IGNORECASE | re.DOTALL,
    )
    _END_RE = re.compile(
        r"\*\*\*\s*END OF (?:THE )?PROJECT GUTENBERG EBOOK.*?\*\*",
        re.IGNORECASE | re.DOTALL,
    )

    text = raw_text
    start_match = _START_RE.search(text)
    end_match = _END_RE.search(text)

    start_idx = start_match.end() if start_match else 0
    end_idx = end_match.start() if end_match else len(text)

    cleaned = text[start_idx:end_idx].strip()
    return cleaned if cleaned else text.strip()


def gutendex_search(page: int = 1, page_size: int = 100, search: str = "") -> Dict:
    params = {
        "languages": "en",
        "page": page,
        "page_size": page_size,
    }

    if search:
        params["search"] = search

    resp = requests.get(GUTENDEX_BASE, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

# =========================
# FILTER HARD GENRES
# =========================
def matches_hard_genre(book_obj: Dict) -> bool:
    subjects = book_obj.get("subjects", [])
    shelves = book_obj.get("bookshelves", [])

    # junta tudo em caixa baixa
    all_tags = " ".join(subjects + shelves).lower()

    for genre in HARD_GENRES:
        if genre.lower() in all_tags:
            return True

    return False


def clean_title_for_filename(title: str) -> str:
    title = unidecode.unidecode(title)
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '_', title)
    title = title.strip('_')

    # limite para evitar erros do Windows
    parts = title.split("_")
    title = "_".join(parts[:6])
    if len(title) > 80:
        title = title[:80]

    return title

# =========================
# MAIN
# =========================
def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    books_downloaded = 0
    page = 1

    while books_downloaded < BOOKS_TO_DOWNLOAD:
        print(f"\n🔎 Procurando livros difíceis na página {page}...")

        data = gutendex_search(page=page, page_size=100)
        results = data.get("results", [])

        if not results:
            print("Nenhum resultado encontrado.")
            break

        for book_obj in results:
            if books_downloaded >= BOOKS_TO_DOWNLOAD:
                break

            if not matches_hard_genre(book_obj):
                continue

            formats = book_obj.get("formats", {})
            text_url = pick_best_text_url(formats)

            if not text_url:
                print(f"[WARN] Livro sem texto: {book_obj['title']}")
                continue

            try:
                raw_text = download_text(text_url)
            except:
                print(f"[ERRO] Falha ao baixar '{book_obj['title']}'")
                continue

            cleaned = strip_gutenberg_boilerplate(raw_text)

            title = book_obj.get("title", "Unknown")
            filename_safe = clean_title_for_filename(title)
            filepath = f"{SAVE_DIR}/{filename_safe}.txt"

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(cleaned)
            except Exception as e:
                print(f"[ERRO ao salvar arquivo]: {e}")
                continue

            print(f"📘 Livro difícil salvo: {filepath}")
            books_downloaded += 1

        page += 1

    print(f"\n🎉 DOWNLOAD CONCLUÍDO: {books_downloaded} livros difíceis baixados!")


if __name__ == "__main__":
    main()
