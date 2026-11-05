"""Comparação objetiva entre grupos de uso de IA (sem interpretação)."""
import pandas as pd

from analysis.exploracao import (
    AUTONOMIA_BAIXA,
    AUTONOMIA_SIM,
    RESP_FREQUENTES,
    SOZINHO,
)


def _fmt(num: int, den: int) -> str:
    """'5 de 12 (41,7%)' ou '—' quando não há respostas."""
    if den == 0:
        return "—"
    return f"{num} de {den} ({num / den * 100:.1f}%)".replace(".", ",")


def comparacao_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por grupo de uso; cada célula mostra 'n de denominador (%)'.

    O denominador de cada coluna são as respostas não vazias daquela pergunta
    dentro do grupo.
    """
    linhas = []
    for grupo in df["grupo_uso"].cat.categories:
        g = df[df["grupo_uso"] == grupo]
        if g.empty:
            continue
        aut, prim, rp = g["autonomia_percebida"], g["primeira_acao"], g["resposta_pronta"]
        linhas.append({
            "Grupo de uso de IA": grupo,
            "Participantes": len(g),
            "Dizem ter autonomia (sim)": _fmt(int(aut.isin(AUTONOMIA_SIM).sum()), int(aut.notna().sum())),
            "Bastante dificuldade ou não conseguem sem IA": _fmt(int(aut.isin(AUTONOMIA_BAIXA).sum()), int(aut.notna().sum())),
            "Tentam resolver sozinhos primeiro": _fmt(int((prim == SOZINHO).sum()), int(prim.notna().sum())),
            "Respostas prontas (frequente/sempre)": _fmt(int(rp.isin(RESP_FREQUENTES).sum()), int(rp.notna().sum())),
        })
    return pd.DataFrame(linhas).set_index("Grupo de uso de IA")