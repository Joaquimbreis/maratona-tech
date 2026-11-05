"""Exporta a base limpa e ANONIMIZADA para análise no Gemini.

Uso (da raiz do projeto, com o .venv ativo), depois de congelar a coleta:
    python -m analysis.exportar data/respostas.xlsx

Gera, na pasta data/:
  - base_gemini.csv        (só as 6 perguntas, sem data/hora nem consentimento)
  - prompt_gemini.txt      (prompt da seção 3.3 do projeto)
  - registro_retrato.txt   (data, n e impressão digital do arquivo enviado)
"""
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from analysis.limpeza import imprimir_relatorio, limpar

PASTA = Path("data")

# Nomes descritivos, para o Gemini entender cada coluna.
COLUNAS_EXPORTACAO = {
    "freq_uso_ia": "Frequencia_uso_IA_nos_estudos",
    "primeira_acao": "Primeira_acao_diante_de_atividade_dificil",
    "resposta_pronta": "Frequencia_uso_resposta_da_IA_sem_tentar_antes",
    "autonomia_percebida": "Percepcao_de_conseguir_estudar_sem_IA",
    "finalidade": "Principal_finalidade_de_uso_da_IA",
    "compreensao": "Frequencia_busca_compreender_o_raciocinio_da_IA",
}

PROMPT = """Analise esta base de dados de uma pesquisa educacional sobre a relação entre Inteligência Artificial e autonomia nos estudos.

A pesquisa investiga se estudantes que utilizam Inteligência Artificial com maior frequência apresentam menor autonomia para resolver atividades escolares.

A hipótese inicial é que estudantes que utilizam IA frequentemente tendem a apresentar menor autonomia e recorrer mais a respostas prontas.

Identifique padrões, frequências, relações entre variáveis e possíveis resultados inesperados.

Não invente informações, não presuma causalidade e não afirme que a hipótese foi confirmada sem evidências estatísticas.

Apresente:
- Principais descobertas.
- Relações entre frequência de uso e autonomia.
- Comportamentos de dependência.
- Possíveis contradições.
- Limitações da pesquisa.
- Conclusões preliminares.

Diferencie claramente observações comprovadas pelos dados de interpretações e sugestões.
"""


def exportar(df_limpo: pd.DataFrame) -> pd.DataFrame:
    """Seleciona só as respostas (como texto), sem carimbo nem sinalizadores."""
    saida = df_limpo[list(COLUNAS_EXPORTACAO)].astype("string")
    saida = saida.rename(columns=COLUNAS_EXPORTACAO)
    saida.insert(0, "ID", range(1, len(saida) + 1))
    return saida


def main(caminho: str) -> None:
    PASTA.mkdir(exist_ok=True)
    bruto = pd.read_excel(caminho) if caminho.endswith(".xlsx") else pd.read_csv(caminho)
    limpo, rel = limpar(bruto)
    imprimir_relatorio(rel)

    saida = exportar(limpo)
    arq_csv = PASTA / "base_gemini.csv"
    saida.to_csv(arq_csv, index=False, encoding="utf-8-sig")
    (PASTA / "prompt_gemini.txt").write_text(PROMPT, encoding="utf-8")

    impressao = hashlib.sha256(arq_csv.read_bytes()).hexdigest()[:16]
    registro = (
        f"Retrato da base enviado ao Gemini\n"
        f"Gerado em: {datetime.now():%d/%m/%Y %H:%M:%S}\n"
        f"Arquivo de origem: {Path(caminho).name}\n"
        f"Respostas válidas (n): {len(saida)}\n"
        f"Impressão digital do CSV (SHA-256, 16 primeiros caracteres): {impressao}\n"
    )
    (PASTA / "registro_retrato.txt").write_text(registro, encoding="utf-8")
    print("\n" + registro)
    print("Arquivos criados em data/: base_gemini.csv, prompt_gemini.txt, registro_retrato.txt")
    print("Revise o CSV antes de enviar: ele não deve ter nome, data/hora ou texto livre.")


if __name__ == "__main__":
    main(sys.argv[1])