import os
import csv
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

PESO_A_SEMANTICO = -0.6166
PESO_B_SINTATICO = 12.6359
INTERCEPTO_C = 651.0517

COMMON_WORDS_PATH = "commonWords/google-10000-english.txt"
BOOKS_DIR = "books/random"
OUTPUT_PATH = "comparation/analise.csv"

def setup_nltk():
    """Verifica se os pacotes 'punkt' e 'punkt_tab' do NLTK estão instalados."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Baixando recursos 'punkt' e 'punkt_tab' do NLTK (necessário para tokenização)...")
        nltk.download('punkt')
        nltk.download('punkt_tab')

def load_common_words(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return set(words)

def analyze_books(common_set, books_dir):
    results = []

    for filename in os.listdir(books_dir):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(books_dir, filename)
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        if not raw_text:
            continue

        # 1. Divide o texto bruto em frases
        sentences = sent_tokenize(raw_text)
        total_sentences = len(sentences)

        # 2. Divide o texto bruto em palavras e converte para minúsculas
        words = word_tokenize(raw_text.lower())
        
        # 3. Limpa a lista de palavras (remove pontuação e mantém apenas palavras)
        clean_words = [word for word in words if word.isalnum()]
        
        total_words = len(clean_words)

        if total_words == 0 or total_sentences == 0:
            print(f"[WARN] Livro '{filename}' parece vazio ou inválido. Pulando.")
            continue

        common_count = sum(1 for w in clean_words if w in common_set)
        percentage_common = (common_count / total_words) * 100
        
        percentage_uncommon = 100.0 - percentage_common

        # 4. Comprimento Médio da Frase (ASL)
        avg_sentence_length = total_words / total_sentences

        score_estimado = (PESO_A_SEMANTICO * percentage_uncommon) + \
                         (PESO_B_SINTATICO * avg_sentence_length) + \
                         INTERCEPTO_C
        
        results.append({
            "book": filename,
            "total_words": total_words,
            "total_sentences": total_sentences, # NOVO
            "avg_sentence_length": round(avg_sentence_length, 2), # NOVO (ASL)
            "common_count": common_count,
            "percentage_common": round(percentage_common, 2),
            "percentage_uncommon": round(percentage_uncommon, 2),
            "score_estimado_L": int(round(score_estimado, 0))
        })
    
    return results

def save_results_to_csv(results, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "book", 
        "total_words", 
        "total_sentences", 
        "avg_sentence_length", 
        "common_count", 
        "percentage_common",
        "percentage_uncommon",
        "score_estimado_L"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Arquivo CSV salvo em: {output_path}")

def main():
    setup_nltk()
    
    common_words_set = load_common_words(COMMON_WORDS_PATH)
    print(f"{len(common_words_set)} palavras comuns carregadas.\n")

    results = analyze_books(common_words_set, BOOKS_DIR) 
    
    if results:
        save_results_to_csv(results, OUTPUT_PATH)
        print("\n=== RESULTADOS SALVOS ===")
        for r in sorted(results, key=lambda x: x['percentage_common'], reverse=True):
            print(f"📘 {r['book']} → {r['percentage_common']}% comuns | ASL: {r['avg_sentence_length']}")
    else:
        print("Nenhum resultado para salvar.")

if __name__ == "__main__":
    main()
