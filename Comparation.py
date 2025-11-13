import os
import csv
import textstat
import nltk

COMMON_WORDS_PATH = "commonWords/google-10000-english.txt"
BOOKS_DIR = "books/randow"
OUTPUT_PATH = "comparation/analise.csv"

def setup_nltk():
    """Verifica se o pacote 'punkt' do NLTK está instalado."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Baixando recursos 'punkt' do NLTK (necessário para textstat)...")
        nltk.download('punkt')

def load_common_words(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return words

def read_book(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().lower()
    for char in ",.!?;:\"'()[]{}<>":
        text = text.replace(char, " ")
    words = text.split()
    return words

def compare_books_with_common_words(common_words, books_dir):
    results = []
    common_set = set(common_words)

    for filename in os.listdir(books_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(books_dir, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                if len(raw_text) < 100:
                    print(f"[WARN] Arquivo {filename} muito curto ou vazio. Pulando.")
                    continue
            except Exception as e:
                print(f"[WARN] Erro ao ler {filename}: {e}")
                continue
            
            words = read_book(filepath)
            if not words:
                continue

            total_words = len(words)
            common_count = sum(1 for w in words if w in common_set)
            percentage = (common_count / total_words) * 100

            # ASL (Average Sentence Length - Média de Palavras por Frase)
            ASL = textstat.avg_sentence_length(raw_text)
            
            # ASW (Average Syllables per Word - Média de Sílabas por Palavra)
            ASW = textstat.avg_syllables_per_word(raw_text)
            
            # FKGL (Flesch-Kincaid Grade Level)
            FKGL_Score = textstat.flesch_kincaid_grade(raw_text)

            results.append({
                "book": filename,
                "total_words": total_words,
                "common_count": common_count,
                "percentage_common": round(percentage, 2),
                "ASL": round(ASL, 2),
                "ASW": round(ASW, 2),
                "FKGL_Score": round(FKGL_Score, 2)
            })
    
    return results

def save_results_to_csv(results, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "book", 
            "total_words", 
            "common_count", 
            "percentage_common",
            "ASL",
            "ASW",
            "FKGL_Score"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Arquivo CSV salvo em: {output_path}")

def main():
    setup_nltk()
    
    common_words = load_common_words(COMMON_WORDS_PATH)
    print(f"{len(common_words)} palavras comuns carregadas.\n")

    results = compare_books_with_common_words(common_words, BOOKS_DIR)
    save_results_to_csv(results, OUTPUT_PATH)

    print("\n=== RESULTADOS SALVOS ===")
    print("--- Ordenado por Nível Flesch-Kincaid (Mais fácil primeiro) ---")

    for r in sorted(results, key=lambda x: x['FKGL_Score']):
        print(f"📘 {r['book']} → Nível FKGL: {r['FKGL_Score']} (% Comum: {r['percentage_common']}%)")

if __name__ == "__main__":
    main()