import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import numpy as np

# ==========================================
# CONFIGURAÇÃO
# ==========================================
BASE_DIR = "comparation"
OUTPUT_DIR = "analysis" # Nova pasta para não misturar

sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

# 1. ORDEM LÓGICA (Controle a ordem das barras aqui)
LOGICAL_ORDER = [
    'children',       
    'moderns_1850',   
    'random',         
    'olds_1850',      
    'har_genres'      
]

# 2. NOMES VISUAIS (Altere os rótulos aqui)
LABEL_MAP = {
    'children':     'Infantil',
    'moderns_1850': 'Moderno (>1900)',
    'random':       'Aleatório',
    'olds_1850':    'Clássico (<1900)',
    'har_genres':   'Técnico/Complexo'
}

# --- Funções de Carregamento (Mantidas) ---
def extract_category_from_filename(filepath):
    filename = os.path.basename(filepath)
    dirname = os.path.basename(os.path.dirname(filepath))
    if dirname != "comparation": return dirname
    if "_" in filename: return filename.split("_")[0]
    return os.path.splitext(filename)[0]

def load_data():
    all_data = []
    files = glob.glob(os.path.join(BASE_DIR, "**", "*.csv"), recursive=True)
    
    if not files:
        print(f"❌ ERRO: Nenhum CSV encontrado em '{BASE_DIR}'")
        return None

    print(f"📂 Lendo {len(files)} arquivos...")
    for filepath in files:
        raw_cat = extract_category_from_filename(filepath)
        cat_lower = raw_cat.lower()
        
        if "child" in cat_lower: cat_key = "children"
        elif "old" in cat_lower: cat_key = "olds_1850"
        elif "modern" in cat_lower: cat_key = "moderns_1850"
        elif "har" in cat_lower: cat_key = "har_genres"
        else: cat_key = "random"

        try:
            df = pd.read_csv(filepath)
            cols_map = {
                'flesch_kincaid_grade': 'FKGL', 'FKGL_Score': 'FKGL',
                'avg_sentence_length': 'ASL', 'nossa_metrica_sintaxe (ASL)': 'ASL',
            }
            df = df.rename(columns=cols_map)
            
            df['category_internal'] = cat_key
            df['category_label'] = LABEL_MAP.get(cat_key, cat_key)
            
            all_data.append(df)
        except: pass

    if not all_data: return None
    return pd.concat(all_data, ignore_index=True)

def get_plot_order(df):
    """Gera a ordem visual dos labels baseada na LOGICAL_ORDER"""
    existing_keys = df['category_internal'].unique()
    final_order = []
    
    for key in LOGICAL_ORDER:
        if key in existing_keys:
            final_order.append(LABEL_MAP.get(key, key))
            
    for key in existing_keys:
        label = LABEL_MAP.get(key, key)
        if label not in final_order:
            final_order.append(label)
    return final_order

# --- ANÁLISE 1: Boxplot de Dificuldade (Mantida) ---
def plot_fkgl_boxplot(df):
    plt.figure(figsize=(10, 6))
    order = get_plot_order(df)

    sns.boxplot(
        x="category_label", 
        y="FKGL", 
        data=df, 
        order=order, 
        palette="Set2",
        linewidth=1.2
    )
    
    plt.ylim(0, 25) 
    plt.title("Nível de Dificuldade Escolar (Flesch-Kincaid) por Categoria")
    plt.ylabel("Anos de Estudo Necessários (FKGL)")
    plt.xlabel("")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = os.path.join(OUTPUT_DIR, "fig1_dificuldade_boxplot.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"✅ Gráfico 1 salvo: {save_path}")

# --- ANÁLISE 2: Barplot de Sintaxe (Nova) ---
def plot_sintaxe_barplot(df):
    plt.figure(figsize=(10, 6))
    order = get_plot_order(df)
    
    # Filtra outliers extremos para o cálculo da média não sujar o gráfico
    df_clean = df[df['ASL'] < 100] 
    
    # Calcula a média por categoria para plotar as barras
    # O Seaborn faz isso automaticamente com o parâmetro estimator=np.mean (padrão)
    # Mas o ci=None remove a barrinha de erro (intervalo de confiança) para ficar mais limpo
    ax = sns.barplot(
        x="category_label", 
        y="ASL", 
        data=df_clean, 
        order=order, 
        palette="viridis", 
        ci=None 
    )
    
    # Adiciona os valores no topo das barras
    for i in ax.containers:
        ax.bar_label(i, fmt='%.1f', padding=3, fontweight='bold')
    
    plt.title("Média de Palavras por Frase (Complexidade Sintática)")
    plt.ylabel("Média (ASL)")
    plt.xlabel("")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = os.path.join(OUTPUT_DIR, "fig2_sintaxe_barplot.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"✅ Gráfico 2 salvo: {save_path}")

def main():
    print("--- Gerando Análise Final (Boxplot + Barplot) ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df = load_data()
    if df is not None:
        df = df[df['FKGL'] <= 40] 
        print(f"Livros processados: {len(df)}")
        
        plot_fkgl_boxplot(df)
        plot_sintaxe_barplot(df)
        
        print(f"\n🎉 Tudo pronto na pasta '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()