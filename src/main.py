import requests
import re
import os
from typing import Dict, Optional

# =========================
# CONFIG
# =========================
GUTENDEX_BASE = "https://gutendex.com/books"
TIMEOUT = 30
# Diretório para salvar os livros baixados
OUTPUT_DIR = "livros_baixados"

# =========================
# GUTENDEX
# =========================
def pick_best_text_url(formats: Dict[str, str]) -> Optional[str]:
    """
    Seleciona a melhor URL de texto plano (plain text) dos formatos disponíveis.
    """
    candidates = [
        "text/plain; charset=utf-8",
        "text/plain; charset=us-ascii",
        "text/plain",
    ]
    for key in candidates:
        if key in formats:
            return formats[key]
    # Fallback para qualquer 'text/plain'
    for k, v in formats.items():
        if k.startswith("text/plain"):
            return v
    return None

def download_text(url: str) -> Optional[str]:
    """
    Baixa o conteúdo de texto de uma URL.
    """
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status() # Verifica se houve erro no request
        if not r.encoding:
            r.encoding = "utf-8"
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"  Erro ao baixar {url}: {e}")
        return None

def gutendex_search_plaintext(query: Optional[str] = None, page: int = 1, page_size = 10) -> Dict:
    """
    Busca na API Gutendex.
    Removido o page_size para usar o padrão da API (32).
    """
    params = {
        "languages": "en",        # Mantido do seu código original
        "page": page,
        "mime_type": "text/plain", # Mantido do seu código original
    }
    if query:
        params["search"] = query
    
    # page_size foi removido, a API usará o padrão (32) [cite: garethbjohnson/gutendex/gutendex-4030b8ad9535b09c69f2b8ced1ba28b1fc42a303/gutendex/settings.py]
    resp = requests.get(GUTENDEX_BASE, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def strip_gutenberg_boilerplate(raw_text: str) -> str:
    """
    Remove o cabeçalho e rodapé padrão dos livros do Gutenberg.
    (Regex corrigido: removido o escape duplo desnecessário de \\s)
    """
    _START_RE = re.compile(r"\s*START OF (?:THE )?PROJECT GUTENBERG EBOOK.?\*", re.IGNORECASE | re.DOTALL)
    _END_RE = re.compile(r"\s*END OF (?:THE )?PROJECT GUTENBERG EBOOK.?\*", re.IGNORECASE | re.DOTALL)
    
    text = raw_text
    start_match = _START_RE.search(text)
    end_match = _END_RE.search(text)

    start_idx = start_match.end() if start_match else 0
    end_idx = end_match.start() if end_match else len(text)

    cleaned = text[start_idx:end_idx].strip()
    return cleaned if cleaned else text.strip()

# =========================
# FUNÇÃO PRINCIPAL (Adaptada para múltiplos livros)
# =========================
def main():
    # 1. Define a consulta
    # Deixando a consulta vazia (None) pegará os mais populares (padrão da API)
    # query = "Pride and Prejudice" 
    query = None 

    # 2. Cria o diretório de saída, se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Salvando livros em: '{os.path.abspath(OUTPUT_DIR)}/'")

    # 3. Busca a primeira página de resultados (padrão de 32)
    try:
        data = gutendex_search_plaintext(query=query, page=1)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar na API: {e}")
        return
        
    # 4. Pega a lista de resultados
    book_list = data.get("results", [])

    if not book_list:
        print("Nenhum livro encontrado para esta consulta.")
        return

    print(f"Encontrados {len(book_list)} livros. Iniciando download...")

    # 5. Itera (faz um loop) por cada livro na lista
    for i, book_obj in enumerate(book_list):
        title = book_obj.get("title", f"livro_desconhecido_{i}").replace("/", "-")
        print(f"\nProcessando {i+1}/{len(book_list)}: '{title}'")

        # 6. Encontra a melhor URL de texto
        formats = book_obj.get("formats", {})
        text_url = pick_best_text_url(formats)
        
        if not text_url:
            print("  Formato de texto não encontrado para este livro.")
            continue # Pula para o próximo livro

        # 7. Baixa o texto bruto
        raw_text = download_text(text_url)
        if not raw_text:
            continue # Pula para o próximo livro

        # 8. Limpa o texto
        cleaned_text = strip_gutenberg_boilerplate(raw_text)

        # 9. Define o nome do arquivo e salva no diretório de saída
        filename = os.path.join(OUTPUT_DIR, f"{title}.txt")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            print(f"  Texto salvo como '{filename}'")
        except IOError as e:
            print(f"  Erro ao salvar o arquivo '{filename}': {e}")
            
    print("\nProcesso concluído.")

if __name__ == "__main__":
    main()
