"""Filtros interativos. Os filtros atuam sobre a BASE (DataFrame), e não só
sobre a aparência dos gráficos: indicadores e gráficos recebem a base já
filtrada."""
import pandas as pd
import streamlit as st

from analysis.limpeza import ESCALA_FREQ, ORDEM

TODAS = "Todas"
CHAVE_USO = "filtro_uso"
CHAVE_AUT = "filtro_autonomia"


def ler_filtros() -> tuple[str, str]:
    """Lê o valor atual dos filtros (antes de desenhá-los na tela)."""
    return (
        st.session_state.get(CHAVE_USO, TODAS),
        st.session_state.get(CHAVE_AUT, TODAS),
    )


def aplicar_filtros(df: pd.DataFrame, uso: str, autonomia: str) -> pd.DataFrame:
    """Devolve só as linhas que atendem aos filtros escolhidos."""
    if uso != TODAS:
        df = df[df["freq_uso_ia"] == uso]
    if autonomia != TODAS:
        df = df[df["autonomia_percebida"] == autonomia]
    return df


def _limpar() -> None:
    """Callback do botão: volta os dois filtros para 'Todas'."""
    st.session_state[CHAVE_USO] = TODAS
    st.session_state[CHAVE_AUT] = TODAS


def renderizar_filtros() -> None:
    """Desenha os filtros. O estado fica em st.session_state (chaves acima),
    então sobrevive à atualização automática de 60 segundos."""
    col1, col2, col3 = st.columns([3, 4, 1.5], vertical_alignment="bottom")
    with col1:
        st.selectbox(
            "Frequência de utilização de IA",
            [TODAS] + ESCALA_FREQ,
            key=CHAVE_USO,
        )
    with col2:
        st.selectbox(
            "Autonomia percebida",
            [TODAS] + ORDEM["autonomia_percebida"],
            key=CHAVE_AUT,
        )
    with col3:
        st.button("Limpar filtros", on_click=_limpar)