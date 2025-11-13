import pandas as pd
from sklearn.linear_model import LinearRegression

ANALISE_CSV_PATH = "comparation/analise.csv"
OFICIAL_CSV_PATH = "comparation/lexile_oficial.csv"

def calibrate_model():
    # 1. Carregar os dados que seu script 'Comparation.py' gerou
    try:
        my_data = pd.read_csv(ANALISE_CSV_PATH)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{ANALISE_CSV_PATH}' não encontrado.")
        print("Por favor, rode 'Comparation.py' (já modificado) primeiro.")
        return

    # 2. Carregar os dados de "verdade" (scores oficiais)
    try:
        official_data = pd.read_csv(OFICIAL_CSV_PATH)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{OFICIAL_CSV_PATH}' não encontrado.")
        print("Certifique-se que o arquivo está em 'comparation/lexile_oficial.csv'")
        return

    # 3. Combinar os dois arquivos usando o nome do livro
    data = pd.merge(my_data, official_data, on="book")

    if data.empty:
        print("Erro: Nenhum livro em comum encontrado entre os dois arquivos CSV.")
        print("Verifique se os nomes dos livros em 'lexile_oficial.csv' batem")
        print("exatamente com os nomes em 'analise.csv'.")
        return

    # Remove linhas onde official_lexile não é numérico (caso 'NP' tenha sobrado)
    data = data[pd.to_numeric(data['official_lexile'], errors='coerce').notnull()]
    data['official_lexile'] = data['official_lexile'].astype(float)

    print(f"Calibrando o modelo com base em {len(data)} livros em comum...")

    # 4. Definir as "features" (X) e o "alvo" (y)
    # X = Nossas duas métricas
    # y = O score Lexile oficial que queremos prever
    
    features = ['percentage_uncommon', 'avg_sentence_length']
    target = 'official_lexile'

    X = data[features]
    y = data[target]

    # 5. Treinar o modelo de Regressão Linear
    model = LinearRegression()
    model.fit(X, y)

    print("\n" + "="*30)
    print("      FÓRMULA ENCONTRADA")
    print("="*30)
    
    coef_semantico_A = model.coef_[0]
    coef_sintatico_B = model.coef_[1]
    intercepto_C = model.intercept_

    print(f"\nScore = ({coef_semantico_A:.4f} * %_Incomum) + ({coef_sintatico_B:.4f} * Média_Frase) + ({intercepto_C:.4f})")
    
    print("\n--- Para usar no seu código: ---")
    print(f"PESO_A_SEMANTICO = {coef_semantico_A:.4f}")
    print(f"PESO_B_SINTATICO = {coef_sintatico_B:.4f}")
    print(f"INTERCEPTO_C = {intercepto_C:.4f}")
    print("="*33)

if __name__ == "__main__":
    calibrate_model()