import os
import requests
import re
import unidecode
from typing import Dict, Optional

# =========================
# CONFIG
# =========================
GUTENDEX_BASE = "https://gutendex.com/books"
TIMEOUT = 10000
BOOKS_TO_DOWNLOAD = 100  

# =========================
# GUTENDEX
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
    _START_RE = re.compile(r"\*\*\*\s*START OF (?:THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE | re.DOTALL)
    _END_RE = re.compile(r"\*\*\*\s*END OF (?:THE )?PROJECT GUTENBERG EBOOK.*?\*\*", re.IGNORECASE | re.DOTALL)
    text = raw_text
    start_match = _START_RE.search(text)
    end_match = _END_RE.search(text)

    start_idx = start_match.end() if start_match else 0
    end_idx = end_match.start() if end_match else len(text)

    cleaned = text[start_idx:end_idx].strip()
    return cleaned if cleaned else text.strip()

def gutendex_search_plaintext(page: int = 1, page_size: int = 100) -> Dict:
    params = {
        "languages": "en",
        "page": page,
        "page_size": page_size,
    }
    resp = requests.get(GUTENDEX_BASE, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def clean_title_for_filename(title: str) -> str:
    title = unidecode.unidecode(title)  # Remove acentuação
    title = re.sub(r'[^\w\s-]', '', title)  # Remove pontuação
    title = re.sub(r'[-\s]+', '_', title)  # Substitui espaços e traços por '_'
    return title.strip('_')

# =========================
# FUNÇÃO PRINCIPAL
# =========================
def main():
    # Inicializa a lista de livros
    books_downloaded = 0

    while books_downloaded < BOOKS_TO_DOWNLOAD:
        # Solicita livros à API
        data = gutendex_search_plaintext(page=1, page_size=100)
        results = data.get("results", [])

        if not results:
            print("Nenhum livro encontrado.")
            break

        for book_obj in results:
            if books_downloaded >= BOOKS_TO_DOWNLOAD:
                break

            # Pega o URL do texto do livro
            formats = book_obj.get("formats", {})
            text_url = pick_best_text_url(formats)
            if not text_url:
                print(f"[WARN] Livro '{book_obj['title']}' não tem formato de texto.")
                continue

            # Baixa o texto do livro
            raw_text = download_text(text_url)

            # Limpa o texto (remove cabeçalho/rodapé do Gutenberg)
            cleaned_text = strip_gutenberg_boilerplate(raw_text)

            # Limpa o título do livro para ser usado como nome de arquivo
            title = book_obj.get("title", "Unknown")
            filename = f"books/randow/{clean_title_for_filename(title)}.txt"

            # Salva o texto em um arquivo .txt
            with open(filename, "w", encoding="utf-8") as f:
                f.write(cleaned_text)

            print(f"Livro '{title}' salvo como '{filename}'")
            books_downloaded += 1

if __name__ == "__main__":
    main()
