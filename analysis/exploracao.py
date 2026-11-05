"""Análise exploratória: frequências, cruzamentos, indicadores e testes.

Todas as funções recebem o DataFrame JÁ LIMPO (saída de limpeza.limpar) e
calculam apenas com os dados reais. Nenhum valor é preenchido ou estimado.

Uso isolado (da raiz do projeto, com o .venv ativo):
    python -m analysis.exploracao data/respostas.xlsx
"""
import sys

import pandas as pd
from scipy import stats

from analysis.limpeza import ORDEM, imprimir_relatorio, limpar

RESP_FREQUENTES = ["Frequentemente", "Sempre"]
AUTONOMIA_SIM = ["Sim, com facilidade", "Sim, mas tenho algumas dificuldades"]
AUTONOMIA_BAIXA = [
    "Tenho bastante dificuldade",
    "Não consigo realizar a maioria das atividades sem IA",
]
PRIMEIRO_IA = [
    "Consulto uma ferramenta de Inteligência Artificial",
    "Peço diretamente a resposta à Inteligência Artificial",
]
SOZINHO = "Tento resolver sozinho antes de procurar ajuda"


def tabela_frequencia(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Contagem e percentual por categoria, na ordem do formulário.

    O percentual usa como denominador só as respostas NÃO em branco.
    """
    contagem = df[coluna].value_counts(sort=False).reindex(ORDEM[coluna], fill_value=0)
    den = int(contagem.sum())
    pct = (contagem / den * 100).round(1) if den else contagem * 0.0
    return pd.DataFrame({"n": contagem, "%": pct})


def cruzamento(df: pd.DataFrame, linha: str, coluna: str) -> pd.DataFrame:
    """Tabela cruzada com contagens absolutas e totais (linhas sem resposta
    em qualquer das duas variáveis ficam de fora, e o total mostra o n)."""
    d = df.dropna(subset=[linha, coluna])
    return pd.crosstab(d[linha], d[coluna], margins=True, margins_name="Total", dropna=False)


def _indicador(rotulo: str, mascara: pd.Series, validos: pd.Series) -> dict:
    """Monta um KPI com numerador, denominador e percentual explícitos."""
    den = int(validos.sum())
    num = int((mascara & validos).sum())
    return {
        "rotulo": rotulo,
        "n": num,
        "den": den,
        "pct": round(num / den * 100, 1) if den else None,
    }


def indicadores(df: pd.DataFrame) -> dict:
    """KPIs do dashboard. O denominador é sempre as respostas não vazias
    daquela pergunta (e muda se o filtro mudar a base)."""
    return {
        "total": len(df),
        "uso_frequente": _indicador(
            "Usam IA frequentemente ou sempre",
            df["freq_uso_ia"].isin(RESP_FREQUENTES), df["freq_uso_ia"].notna()),
        "tenta_sozinho": _indicador(
            "Tentam resolver sozinhos primeiro",
            df["primeira_acao"] == SOZINHO, df["primeira_acao"].notna()),
        "resposta_pronta": _indicador(
            "Usam respostas prontas frequentemente ou sempre",
            df["resposta_pronta"].isin(RESP_FREQUENTES), df["resposta_pronta"].notna()),
        "autonomia": _indicador(
            "Afirmam conseguir estudar sem depender de IA",
            df["autonomia_percebida"].isin(AUTONOMIA_SIM), df["autonomia_percebida"].notna()),
    }


def spearman(df: pd.DataFrame, x: str, y: str) -> dict:
    """Correlação de Spearman entre duas colunas de códigos ordinais."""
    d = df[[x, y]].dropna()
    if len(d) < 3 or d[x].nunique() < 2 or d[y].nunique() < 2:
        return {"n": len(d), "rho": None, "p": None}
    rho, p = stats.spearmanr(d[x], d[y])
    return {"n": len(d), "rho": round(float(rho), 2), "p": round(float(p), 3)}


# Pares testados. Em "autonomia_cod", maior valor = mais autonomia.
PARES = [
    ("freq_uso_ia_cod", "autonomia_cod", "Uso de IA × autonomia percebida"),
    ("freq_uso_ia_cod", "resposta_pronta_cod", "Uso de IA × respostas prontas"),
    ("freq_uso_ia_cod", "compreensao_cod", "Uso de IA × compreensão do raciocínio"),
]


def testes(df: pd.DataFrame, excluir_inconsistentes: bool = False) -> pd.DataFrame:
    """Tabela com os testes de associação (exploratórios, sem correção para
    comparações múltiplas). Com excluir_inconsistentes=True, retira quem
    marcou 'Nunca' mas respondeu sobre uso (análise de sensibilidade)."""
    base = df[~df["inconsistente"]] if excluir_inconsistentes else df
    linhas = []
    for x, y, nome in PARES:
        r = spearman(base, x, y)
        linhas.append({"Associação": nome, "n": r["n"], "rho": r["rho"], "p": r["p"]})
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    caminho = sys.argv[1]
    bruto = pd.read_excel(caminho) if caminho.endswith(".xlsx") else pd.read_csv(caminho)
    limpo, rel = limpar(bruto)
    imprimir_relatorio(rel)

    print("\n== Indicadores ==")
    for k, v in indicadores(limpo).items():
        print(f"{k}: {v}")

    for col in ["freq_uso_ia", "primeira_acao", "resposta_pronta",
                "autonomia_percebida", "finalidade", "compreensao"]:
        print(f"\n== {col} ==")
        print(tabela_frequencia(limpo, col).to_string())

    print("\n== Uso (grupo) x autonomia ==")
    print(cruzamento(limpo, "grupo_uso", "autonomia_percebida").to_string())
    print("\n== Uso (grupo) x primeira ação ==")
    print(cruzamento(limpo, "grupo_uso", "primeira_acao").to_string())
    print("\n== Uso (grupo) x respostas prontas ==")
    print(cruzamento(limpo, "grupo_uso", "resposta_pronta").to_string())

    print("\n== Testes (Spearman) ==")
    print(testes(limpo).to_string(index=False))
    print("\n== Testes sem os 'inconsistentes' ==")
    print(testes(limpo, excluir_inconsistentes=True).to_string(index=False))