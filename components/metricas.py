"""Cartões de indicadores (KPIs) com denominador explícito."""
import streamlit as st

ESTILO = """
<style>
[data-testid="stMetric"] {
    background: #111B2E; border: 1px solid #1F2E4A;
    border-radius: 10px; padding: 14px 16px;
}
[data-testid="stMetricValue"] { color: #3B82F6; }
</style>
"""


def aplicar_estilo() -> None:
    """Injeta o CSS dos cartões (tema dark com destaque azul)."""
    st.markdown(ESTILO, unsafe_allow_html=True)


def formatar_kpi(ind: dict) -> tuple[str, str]:
    """Transforma um indicador em (valor, legenda). Ex.: ('66,7%', '12 de 18')."""
    if ind["pct"] is None:
        return "—", "sem respostas"
    valor = f"{ind['pct']:.1f}".replace(".", ",") + "%"
    return valor, f"{ind['n']} de {ind['den']}"


def renderizar_kpis(ind: dict) -> None:
    """Desenha os 5 cartões: total + 4 percentuais."""
    cols = st.columns(5)
    cols[0].metric("Participantes válidos", ind["total"])
    for col, chave in zip(
        cols[1:], ["uso_frequente", "tenta_sozinho", "resposta_pronta", "autonomia"]
    ):
        valor, legenda = formatar_kpi(ind[chave])
        col.metric(ind[chave]["rotulo"], valor, help=f"Base: {legenda} respostas")
        col.caption(legenda)