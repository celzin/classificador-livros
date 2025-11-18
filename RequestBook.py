import os
import requests
import re
import pandas as pd  # Para ler e processar o CSV
import time
from typing import Dict, Optional

# =========================
# CONFIG
# =========================
GUTENDEX_BASE = "https://gutendex.com/books"
TIMEOUT = 10
BOOKS_TO_DOWNLOAD = 100  # Limite de livros para baixar

# Caminho para o arquivo CSV bruto que você baixou do CORGIS
LOCAL_CSV_PATH = "comparation/classics.csv" 
# Onde salvaremos nosso gabarito limpo e processado
MASTER_GABARITO_PATH = "comparation/gabarito_master.csv"
# Pasta de destino dos livros
BOOKS_DIR = "books/random" # Usando 'random'

# =========================
# FUNÇÕES DE HELPER (Mantidas do seu script )
# =========================
def pick_best_text_url(formats: Dict[str, str]) -> Optional[str]:
    """
    Encontra o melhor URL de texto puro, priorizando UTF-8
    e explicitamente REJEITANDO arquivos .zip.
    """
    candidates = [
        "text/plain; charset=utf-8",
        "text/plain; charset=us-ascii",
        "text/plain",
    ]
    
    url_encontrada = None

    # 1. Tenta encontrar a melhor correspondência (UTF-8, etc.) que NÃO seja zip
    for key in candidates:
        if key in formats:
            url = formats[key]
            # A API às vezes lista um .zip sob a chave 'text/plain'
            if not url.endswith(".zip"): 
                url_encontrada = url
                # Encontramos a melhor (ex: .../1342.txt.utf-8)
                return url_encontrada 

    # 2. Se falharmos (porque só encontramos .zip ou nada nos 'candidates'),
    # procuramos por qualquer URL que seja 'text/plain' E termine em '.txt'
    for key, url in formats.items():
        if key.startswith("text/plain") and url.endswith(".txt"):
            return url # Encontramos uma que é explicitamente .txt (ex: .../100-0.txt)

    # 3. Se ainda assim falharmos, pegamos a primeira 'text/plain' que
    # encontrarmos que não seja .zip (cobre outros casos)
    for key, url in formats.items():
         if key.startswith("text/plain") and not url.endswith(".zip"):
            return url

    # Se tudo o que encontramos foram .zip ou links .html, retornamos None
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

# =========================
# NOVAS FUNÇÕES
# =========================

def get_book_by_id(book_id: int) -> Optional[Dict]:
    """Busca um livro específico na API Gutendex usando sua ID."""
    try:
        url = f"{GUTENDEX_BASE}/{book_id}"
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[WARN] Falha ao buscar API para ID {book_id}: {e}")
        return None

def process_master_catalog():
    """
    Lê o CSV 'classics.csv' local, extrai as colunas corretas,
    calcula o ASW, e salva o 'gabarito_master.csv' limpo.
    """
    os.makedirs(os.path.dirname(MASTER_GABARITO_PATH), exist_ok=True)
    
    if os.path.exists(MASTER_GABARITO_PATH):
        print(f"Catálogo mestre '{MASTER_GABARITO_PATH}' já existe. Usando cache.")
        return pd.read_csv(MASTER_GABARITO_PATH)

    print(f"Lendo gabarito local de '{LOCAL_CSV_PATH}'...")
    try:
        df = pd.read_csv(LOCAL_CSV_PATH)
        
        # --- CORREÇÃO IMPORTANTE ---
        # Nomes exatos das colunas do seu CSV 
        col_id = "metadata.id"
        col_title = "bibliography.title"
        col_author = "bibliography.author.name"
        col_fkgl = "metrics.difficulty.flesch kincaid grade" # Com espaço
        col_asl = "metrics.statistics.average sentence length" # Com espaços
        col_syllables = "metrics.statistics.syllables"
        col_words = "metrics.statistics.words"
        # A coluna que você mencionou ("average sentence per word") é 1/ASL, então vamos ignorá-la
        # e calcular o ASW (avg syllables per word) nós mesmos.
        
        colunas_necessarias = [
            col_id, col_title, col_author, col_fkgl, 
            col_asl, col_syllables, col_words
        ]

        # Verifica se todas as colunas existem
        for col in colunas_necessarias:
            if col not in df.columns:
                raise KeyError(f"Coluna necessária não encontrada no CSV: '{col}'")

        # Filtra o DataFrame
        df_cleaned = df[colunas_necessarias].copy()
        
        # Limpa dados: remove linhas com valores nulos em colunas críticas
        df_cleaned = df_cleaned.dropna()
        
        # Calcula o ASW (Average Syllables per Word)
        # Evita divisão por zero
        df_cleaned = df_cleaned[df_cleaned[col_words] > 0]
        df_cleaned['ASW_Gabarito'] = df_cleaned[col_syllables] / df_cleaned[col_words]
        
        # Renomeia as colunas para nomes mais amigáveis
        df_final = df_cleaned.rename(columns={
            col_id: "book_id",
            col_title: "title",
            col_author: "author",
            col_fkgl: "FKGL_Score_Gabarito",
            col_asl: "ASL_Gabarito"
        })
        
        # Mantém apenas as colunas que realmente usaremos
        colunas_finais = [
            "book_id", "title", "author", 
            "FKGL_Score_Gabarito", "ASL_Gabarito", "ASW_Gabarito"
        ]
        df_final = df_final[colunas_finais]

        # Garante que book_id seja um inteiro
        df_final['book_id'] = df_final['book_id'].astype(int)

        # Salva nosso novo gabarito limpo
        df_final.to_csv(MASTER_GABARITO_PATH, index=False, encoding='utf-8')
        print(f"Gabarito mestre limpo salvo em '{MASTER_GABARITO_PATH}'")
        return df_final
        
    except FileNotFoundError:
        print(f"ERRO: O arquivo '{LOCAL_CSV_PATH}' não foi encontrado.")
        print(f"Por favor, baixe o arquivo de 'https://corgis-edu.github.io/corgis/csv/classics/classics.csv' e salve-o nessa pasta.")
        return None
    except KeyError as e:
        print(f"ERRO: {e}")
        print("Verifique se o arquivo 'classics.csv' é a versão correta do CORGIS.")
        return None
    except Exception as e:
        print(f"Falha ao processar o catálogo mestre: {e}")
        return None

# =========================
# FUNÇÃO PRINCIPAL (Inalterada da Versão 4)
# =========================
def main():
    # Passo 1: Carregar (ou criar) nosso gabarito mestre
    df_gabarito = process_master_catalog()
    if df_gabarito is None:
        print("Não foi possível carregar o catálogo. Abortando.")
        return
        
    print(f"Catálogo mestre carregado. {len(df_gabarito)} livros com scores válidos encontrados.")
    
    os.makedirs(BOOKS_DIR, exist_ok=True)

    # Passo 2: Iterar pelo gabarito e baixar os livros .txt
    books_downloaded_count = 0
    print(f"Iniciando download de até {BOOKS_TO_DOWNLOAD} livros...")

    for index, row in df_gabarito.iterrows():
        
        if books_downloaded_count >= BOOKS_TO_DOWNLOAD:
            print(f"Limite de {BOOKS_TO_DOWNLOAD} livros atingido.")
            break
        
        book_id = row['book_id']
        book_title = row['title']
        
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
            print(f"[WARN] Livro ID {book_id} ('{book_title}') não tem formato .txt. (Pulando)")
            continue

        try:
            raw_text = download_text(text_url)
        except requests.RequestException:
            continue

        cleaned_text = strip_gutenberg_boilerplate(raw_text)
        if not cleaned_text:
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"({books_downloaded_count + 1}/{BOOKS_TO_DOWNLOAD}) Livro ID {book_id} ('{book_title}') salvo.")
        books_downloaded_count += 1
        
        time.sleep(0.1) 

    print(f"\nDownload concluído. Total de {books_downloaded_count} novos livros baixados.")
    print(f"A pasta '{BOOKS_DIR}' e o arquivo '{MASTER_GABARITO_PATH}' estão prontos.")

if __name__ == "__main__":
    main()