import os
import csv

COMMON_WORDS_PATH = "commonWords/google-10000-english-usa-no-swears-short.txt"
BOOKS_DIR = "books/hard_genres"
OUTPUT_PATH = "comparation/analise.csv"

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
            words = read_book(filepath)
            if not words:
                continue

            total_words = len(words)
            common_count = sum(1 for w in words if w in common_set)
            percentage = (common_count / total_words) * 100

            results.append({
                "book": filename,
                "total_words": total_words,
                "common_count": common_count,
                "percentage_common": round(percentage, 2)
            })
    
    return results

def save_results_to_csv(results, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # cria pasta comparation se não existir

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["book", "total_words", "common_count", "percentage_common"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Arquivo CSV salvo em: {output_path}")

def main():
    common_words = load_common_words(COMMON_WORDS_PATH)
    print(f"{len(common_words)} palavras comuns carregadas.\n")

    results = compare_books_with_common_words(common_words, BOOKS_DIR)
    save_results_to_csv(results, OUTPUT_PATH)

    print("\n=== RESULTADOS SALVOS ===")
    for r in results:
        print(f"📘 {r['book']} → {r['percentage_common']}% de palavras comuns")

if __name__ == "__main__":
    main()
