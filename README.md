# 📚 Avaliação de Dificuldade de Leitura na Literatura Inglesa 

Este projeto é um sistema exploratório de **Ciência de Dados** desenvolvido para classificar a dificuldade de leitura de obras literárias em inglês.

O sistema analisa textos de domínio público (Project Gutenberg) e arquivos locais, calculando métricas de leiturabilidade e densidade lexical para categorizar obras em diferentes níveis de proficiência (do infantil ao acadêmico/complexo).

## 📂 Estrutura do Projeto

* `/books_pdf`: Diretório para inserção de arquivos PDF locais para análise.
* `/books`: Diretório onde os textos processados (.txt) são armazenados.
* `/commomWords`: Diretório contendo vocabulário comum baseado na lista Google-10000 English.
* `/comparation`: Diretório com os resultados comparativos gerados.
* `/src`: Contém os scripts Python de coleta, processamento e análise.

## 🚀 Funcionalidades

* **Ingestão de Dados via API:** Coleta automática de metadados e textos do Project Gutenberg utilizando a API Gutendex.
* **Processamento de Arquivos Locais (PDF):** Conversão automática de livros em PDF para texto plano (.txt) para análise.
* **Cálculo de Métricas de Leiturabilidade:**
    * *Flesch-Kincaid Grade Level (FKGL):* Estima a escolaridade necessária para leitura.
    * *Average Sentence Length (ASL):* Complexidade sintática baseada no tamanho das frases.
    * *Average Syllables per Word (ASW):* Complexidade morfológica.
    * *Cobertura Vocabular:* Percentual de palavras comuns baseado na lista *Google-10000 English*.
* **Visualização de Dados:** Geração de gráficos (Boxplots e Barplots) para comparação entre categorias literárias.

## 👥 Autores

<table align="center">
  <tr>
    <th>Autor</th>
    <th>Contato</th>
  </tr>
  <tr>
    <td>Celso Vinícius</td>
    <td><a href="https://www.linkedin.com/in/celsovinicius23/"><img align="center" height="20px" width="90px" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/> </td>
  </tr>
  <tr>
    <td>Luan Gonçalves</td>
    <td><a href="https://www.linkedin.com/in/luan-santos-9bb01920b/"><img align="center" height="20px" width="90px" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/> </td>
  </tr>
</table>