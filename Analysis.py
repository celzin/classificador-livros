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

# --- Funções de Carregamento (Iguais ao anterior) ---
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
        cat = extract_category_from_filename(filepath)
        try:
            df = pd.read_csv(filepath)
            # Normaliza colunas
            cols_map = {
                'flesch_kincaid_grade': 'FKGL', 'FKGL_Score': 'FKGL',
                'avg_sentence_length': 'ASL', 'nossa_metrica_sintaxe (ASL)': 'ASL',
                'ASW_textstat': 'ASW',
                'percentage_uncommon': 'Perc_Uncommon', 'nossa_metrica_semantica (%incomum)': 'Perc_Uncommon'
            }
            df = df.rename(columns=cols_map)
            df['category'] = cat
            all_data.append(df)
        except: pass

    if not all_data: return None
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Garante % Incomum
    if 'Perc_Uncommon' not in final_df.columns and 'percentage_common' in final_df.columns:
        final_df['Perc_Uncommon'] = 100 - final_df['percentage_common']
        
    return final_df

# --- NOVAS ANÁLISES ---

def plot_vocabulary_ranking(df):
    """
    Gráfico de Barras: Quem usa o vocabulário mais difícil?
    Compara a média de % Palavras Incomuns por categoria.
    """
    plt.figure(figsize=(10, 6))
    
    # Agrupa por categoria e calcula média
    ranking = df.groupby("category")["Perc_Uncommon"].mean().sort_values()
    
    # Gráfico de Barras Horizontal
    barplot = sns.barplot(
        x=ranking.values, 
        y=ranking.index, 
        palette="magma"
    )
    
    # Adiciona o valor na ponta da barra
    for i, v in enumerate(ranking.values):
        barplot.text(v + 0.1, i, f"{v:.1f}%", va='center', fontweight='bold')

    plt.title("Ranking de Raridade Vocabular (% de Palavras Incomuns)")
    plt.xlabel("Porcentagem Média de Palavras Incomuns")
    plt.ylabel("Categoria")
    plt.tight_layout()
    
    plt.savefig(os.path.join(OUTPUT_DIR, "fig2_ranking_vocabulario.png"))
    plt.close()
    print("✅ Gráfico salvo: fig2_ranking_vocabulario.png")

def plot_sentence_len_ranking(df):
    """
    Gráfico de Barras: Quem escreve as frases mais longas?
    Compara a média de ASL (Palavras por Frase).
    """
    plt.figure(figsize=(10, 6))
    
    # Filtra outliers extremos para não distorcer a média
    df_clean = df[df['ASL'] < 100]
    ranking = df_clean.groupby("category")["ASL"].mean().sort_values()
    
    barplot = sns.barplot(
        x=ranking.values, 
        y=ranking.index, 
        palette="viridis"
    )
    
    for i, v in enumerate(ranking.values):
        barplot.text(v + 0.5, i, f"{v:.1f}", va='center', fontweight='bold')

    plt.title("Ranking de Complexidade Sintática (Tamanho da Frase)")
    plt.xlabel("Média de Palavras por Frase (ASL)")
    plt.ylabel("Categoria")
    plt.tight_layout()
    
    plt.savefig(os.path.join(OUTPUT_DIR, "fig3_ranking_sintaxe.png"))
    plt.close()
    print("✅ Gráfico salvo: fig3_ranking_sintaxe.png")

def plot_correlation_heatmap(df):
    """
    Matriz de Correlação: Como as variáveis se relacionam?
    Isso é pura Ciência de Dados. Mostra o que influencia o quê.
    """
    plt.figure(figsize=(8, 6))
    
    # Seleciona apenas colunas numéricas relevantes
    cols = ['FKGL', 'ASL', 'ASW', 'Perc_Uncommon']
    # Filtra erros de leitura
    df_clean = df[df['FKGL'] <= 30]
    
    corr = df_clean[cols].corr()
    
    sns.heatmap(
        corr, 
        annot=True,     # Escreve o número no quadrado
        cmap="coolwarm", # Azul (negativo) a Vermelho (positivo)
        fmt=".2f", 
        vmin=-1, vmax=1
    )
    
    plt.title("Matriz de Correlação das Métricas")
    plt.tight_layout()
    
    plt.savefig(os.path.join(OUTPUT_DIR, "fig4_heatmap_correlacao.png"))
    plt.close()
    print("✅ Gráfico salvo: fig4_heatmap_correlacao.png")

def plot_fkgl_boxplot(df):
    """O gráfico que você gostou (mantido)"""
    plt.figure(figsize=(10, 6))
    try:
        order = df.groupby("category")["FKGL"].median().sort_values().index
    except: return

    sns.boxplot(x="category", y="FKGL", data=df, order=order, palette="Set2")
    
    plt.ylim(0, 20) # Focando na faixa escolar real (0 a 20 anos)
    plt.title("Comparação de Dificuldade Geral (FKGL) por Categoria")
    plt.ylabel("Nível Escolar (Anos de Estudo)")
    plt.xlabel("Categoria")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(os.path.join(OUTPUT_DIR, "fig1_fkgl_boxplot.png"))
    plt.close()
    print("✅ Gráfico salvo: fig1_fkgl_boxplot.png")

def main():
    print("--- Iniciando Análise V2 ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df = load_data()
    if df is not None:
        # Filtra outliers gerais para análise limpa
        df = df[df['FKGL'] <= 30] 
        
        print(f"Livros válidos para análise: {len(df)}")
        
        plot_fkgl_boxplot(df)       # O Boxplot (Visualizar distribuição)
        plot_vocabulary_ranking(df) # Barplot (Comparar Vocabulário)
        plot_sentence_len_ranking(df) # Barplot (Comparar Sintaxe)
        plot_correlation_heatmap(df) # Heatmap (Entender a relação matemática)
        
        print(f"\n🎉 Resultados salvos na pasta '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()