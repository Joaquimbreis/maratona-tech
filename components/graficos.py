"""Gráficos Plotly (tema dark, destaque azul).

Cada gráfico tem duas partes: uma função `dados_*` (só Pandas, fácil de
conferir) e uma função `grafico_*` que desenha a figura. Todas recebem a
base JÁ FILTRADA e devolvem None quando não há dados para mostrar.
"""
import pandas as pd
import plotly.graph_objects as go

from analysis.limpeza import ESCALA_FREQ, ORDEM

AZUL = "#3B82F6"
TEXTO = "#E5E7EB"
GRADE = "#1F2E4A"

# Da MAIOR para a MENOR autonomia: azul -> cinza -> âmbar -> vermelho.
CORES_AUTONOMIA = {
    "Sim, com facilidade": "#2563EB",
    "Sim, mas tenho algumas dificuldades": "#60A5FA",
    "Depende da atividade": "#94A3B8",
    "Tenho bastante dificuldade": "#F59E0B",
    "Não consigo realizar a maioria das atividades sem IA": "#EF4444",
}
ROTULO_AUTONOMIA = {
    "Sim, com facilidade": "Com facilidade",
    "Sim, mas tenho algumas dificuldades": "Com algumas dificuldades",
    "Depende da atividade": "Depende da atividade",
    "Tenho bastante dificuldade": "Bastante dificuldade",
    "Não consigo realizar a maioria das atividades sem IA": "Não consigo sem IA",
}
# Frequência de respostas prontas: do azul claro (nunca) ao azul escuro (sempre).
CORES_FREQ = {
    "Nunca": "#BFDBFE", "Raramente": "#93C5FD", "Às vezes": "#60A5FA",
    "Frequentemente": "#2563EB", "Sempre": "#1D4ED8",
}


def _layout(fig: go.Figure, titulo: str, altura: int = 430) -> go.Figure:
    """Aparência comum a todos os gráficos."""
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16)),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXTO),
        height=altura,
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor=GRADE)
    fig.update_yaxes(gridcolor=GRADE)
    return fig


# ----------------------------------------------------------------------
# Gráfico 1: frequência de utilização de IA
# ----------------------------------------------------------------------
def dados_frequencia(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem e percentual de cada frequência de uso."""
    cont = df["freq_uso_ia"].value_counts(sort=False).reindex(ESCALA_FREQ, fill_value=0)
    total = int(cont.sum())
    pct = (cont / total * 100).round(1) if total else cont * 0.0
    return pd.DataFrame({"categoria": ESCALA_FREQ, "n": cont.values, "pct": pct.values})


def grafico_frequencia(df: pd.DataFrame):
    """Barras: quantos estudantes em cada frequência de uso."""
    d = dados_frequencia(df)
    total = int(d["n"].sum())
    if total == 0:
        return None
    fig = go.Figure(go.Bar(
        x=d["categoria"], y=d["n"], marker_color=AZUL,
        text=[f"{n} ({p:.0f}%)" for n, p in zip(d["n"], d["pct"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{y} estudantes<extra></extra>",
    ))
    fig.update_yaxes(title_text="Participantes", range=[0, d["n"].max() * 1.25])
    return _layout(fig, f"Frequência de utilização de IA (n={total})")


# ----------------------------------------------------------------------
# Gráficos 2 e 3: cruzamentos por grupo de uso
# ----------------------------------------------------------------------
def dados_cruzamento(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Contagens: grupos de uso (linhas) x respostas de `coluna` (colunas).

    Quem deixou `coluna` em branco fica de fora; grupos sem ninguém somem.
    """
    d = df.dropna(subset=["grupo_uso", coluna])
    grupos = list(df["grupo_uso"].cat.categories)
    tab = pd.crosstab(d["grupo_uso"], d[coluna]).reindex(
        index=grupos, columns=ORDEM[coluna], fill_value=0
    )
    return tab[tab.sum(axis=1) > 0]


def _barras_empilhadas(tab, titulo, cores, rotulos, percentual):
    """Barras empilhadas por grupo de uso, com o n de cada grupo no eixo."""
    totais = tab.sum(axis=1)
    x = [f"{g}<br>(n={int(totais[g])})" for g in tab.index]
    fig = go.Figure()
    for cat in tab.columns: 
        valores = tab[cat]
        nome = rotulos.get(cat, cat)
        if percentual:
            y = (valores / totais * 100).round(1)
            texto = [f"{v:.0f}%" if v > 0 else "" for v in y]
        else:
            y = valores
            texto = [str(int(v)) if v > 0 else "" for v in valores]
        fig.add_trace(go.Bar(
            name=nome, x=x, y=y, marker_color=cores[cat],
            text=texto, textposition="inside",
            customdata=valores,
            hovertemplate="%{x}<br>" + nome + ": %{customdata} resp.<extra></extra>",
        ))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="% dentro do grupo" if percentual else "Participantes")
    fig.update_xaxes(title_text="Frequência de uso de IA (agrupada)")
    return _layout(fig, titulo)


def grafico_uso_autonomia(df: pd.DataFrame, percentual: bool = False):
    """Barras empilhadas: grupo de uso x autonomia percebida."""
    tab = dados_cruzamento(df, "autonomia_percebida")
    if tab.empty:
        return None
    return _barras_empilhadas(
        tab, f"Uso de IA × autonomia percebida (n={int(tab.values.sum())})",
        CORES_AUTONOMIA, ROTULO_AUTONOMIA, percentual,
    )


def grafico_resposta_pronta(df: pd.DataFrame, percentual: bool = False):
    """Barras empilhadas: grupo de uso x uso de respostas prontas."""
    tab = dados_cruzamento(df, "resposta_pronta")
    if tab.empty:
        return None
    return _barras_empilhadas(
        tab, f"Uso de respostas prontas por grupo de uso (n={int(tab.values.sum())})",
        CORES_FREQ, {}, percentual,
    )
