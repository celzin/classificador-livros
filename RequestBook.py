import os
import requests
import re
import pandas as pd
import time
from typing import Dict, Optional

GUTENDEX_BASE = "https://gutendex.com/books"
TIMEOUT = 30
BOOKS_TO_DOWNLOAD = 30 

LOCAL_CSV_PATH = "docs/classics.csv" 
MASTER_GABARITO_PATH = "comparation/gabarito.csv"
BOOKS_DIR = "books/random" 

def pick_best_text_url(formats: Dict[str, str]) -> Optional[str]:
    candidates = [
        "text/plain; charset=utf-8",
        "text/plain; charset=us-ascii",
        "text/plain",
    ]
    
    for key in candidates:
        if key in formats:
            url = formats[key]
            if not url.endswith(".zip"): 
                return url 

    for key, url in formats.items():
        if key.startswith("text/plain") and url.endswith(".txt"):
            return url 

    for key, url in formats.items():
         if key.startswith("text/plain") and not url.endswith(".zip"):
            return url

    return None

def download_text(url: str) -> str:
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if not r.encoding:
                r.encoding = "utf-8"
            return r.text
        except requests.RequestException:
            time.sleep(2)
    return ""

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

def get_book_by_id(book_id: int, retries=3) -> Optional[Dict]:
    """
    Busca um livro específico na API com mecanismo de RE-TENTATIVA.
    Se falhar, espera um pouco e tenta de novo.
    """
    url = f"{GUTENDEX_BASE}/{book_id}"
    
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < retries - 1:
                sleep_time = 2 * (attempt + 1) # Backoff: espera 2s, depois 4s...
                print(f"[INFO] Timeout ID {book_id}. Tentando novamente em {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"[WARN] Falha ao buscar API para ID {book_id} após {retries} tentativas.")
                return None
    return None

def load_master_catalog():
    os.makedirs(os.path.dirname(MASTER_GABARITO_PATH), exist_ok=True)
    
    if os.path.exists(MASTER_GABARITO_PATH):
        print(f"Catálogo mestre '{MASTER_GABARITO_PATH}' já existe. Usando cache.")
        return pd.read_csv(MASTER_GABARITO_PATH)

    print(f"Lendo gabarito local de '{LOCAL_CSV_PATH}'...")
    try:
        df = pd.read_csv(LOCAL_CSV_PATH)
        
        rename_map = {
            "metadata.id": "book_id",
            "bibliography.title": "title",
            "metrics.difficulty.flesch kincaid grade": "FKGL_Score_Gabarito",
            # Adicione outras colunas aqui se precisar
        }
        
        available_cols = [c for c in rename_map.keys() if c in df.columns]
        df_cleaned = df[available_cols].copy()
        df_cleaned.rename(columns=rename_map, inplace=True)
        
        df_cleaned = df_cleaned.dropna()
        df_cleaned['book_id'] = df_cleaned['book_id'].astype(int)

        df_cleaned.to_csv(MASTER_GABARITO_PATH, index=False, encoding='utf-8')
        print(f"Gabarito mestre salvo em '{MASTER_GABARITO_PATH}'")
        return df_cleaned
        
    except Exception as e:
        print(f"Falha ao processar o catálogo mestre: {e}")
        return None

def main():
    df_gabarito = load_master_catalog()
    if df_gabarito is None:
        return
        
    print(f"Catálogo carregado. Iniciando downloads...")
    os.makedirs(BOOKS_DIR, exist_ok=True)

    books_downloaded_count = 0
    
    for index, row in df_gabarito.iterrows():
        if books_downloaded_count >= BOOKS_TO_DOWNLOAD:
            print(f"Limite de {BOOKS_TO_DOWNLOAD} livros atingido.")
            break
        
        book_id = row['book_id']
        book_title = row.get('title', 'Unknown')
        
        filename = f"{book_id}.txt"
        filepath = os.path.join(BOOKS_DIR, filename)

        if os.path.exists(filepath):
            continue 

        book_obj = get_book_by_id(book_id)
        if not book_obj:
            continue

        formats = book_obj.get("formats", {})
        text_url = pick_best_text_url(formats)
        
        if not text_url:
            print(f"[WARN] Livro ID {book_id} ('{book_title}') sem formato txt adequado. (Pulando)")
            continue

        raw_text = download_text(text_url)
        if not raw_text:
            continue

        cleaned_text = strip_gutenberg_boilerplate(raw_text)
        if not cleaned_text:
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"({books_downloaded_count + 1}/{BOOKS_TO_DOWNLOAD}) Livro ID {book_id} salvo.")
        books_downloaded_count += 1
        
        time.sleep(1) 

    print(f"\nDownload concluído.")

if __name__ == "__main__":
    main()