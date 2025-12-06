import os
import fitz  # PyMuPDF
import shutil

# =========================
# CONFIGURAÇÕES
# =========================
INPUT_DIR = "booksPDF"
OUTPUT_DIR = "books/random"

def extract_text_from_pdf(pdf_path):
    """Lê um PDF e retorna o texto completo."""
    print(f"   📖 Lendo: {os.path.basename(pdf_path)}...")
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"   ❌ Erro ao ler PDF: {e}")
        return None
    return text

def process_folder():
    # 1. Garante que as pastas existem
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"📂 Pasta '{INPUT_DIR}' criada! Coloque seus PDFs lá.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Lista arquivos na pasta de entrada
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not files:
        print(f"📭 A pasta '{INPUT_DIR}' está vazia (sem arquivos .pdf).")
        return

    print(f"🚀 Encontrados {len(files)} livros para processar em '{INPUT_DIR}'...")

    count = 0
    for filename in files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        
        # Extrai texto
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            # Cria nome do arquivo .txt (ex: "O Pequeno Principe.pdf" -> "O_Pequeno_Principe.txt")
            safe_name = "".join([c for c in filename if c.isalnum() or c in (' ', '-', '_')]).strip()
            txt_filename = os.path.splitext(safe_name.replace(" ", "_"))[0] + ".txt"
            output_path = os.path.join(OUTPUT_DIR, txt_filename)
            
            # Salva no destino
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            print(f"   ✅ Convertido: {txt_filename}")
            count += 1
        else:
            print(f"   ⚠️ Falha ao converter {filename}")

    print(f"\n✨ Processamento concluído! {count} livros novos em '{OUTPUT_DIR}'.")
    print("👉 Agora rode 'python Comparation.py' para ver a classificação.")

if __name__ == "__main__":
    process_folder()