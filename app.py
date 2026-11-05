"""Dashboard: Inteligência Artificial e Autonomia nos Estudos (Maratona Tech)."""
from datetime import datetime

import streamlit as st

from analysis.exploracao import indicadores
from analysis.limpeza import limpar
from components.filtros import aplicar_filtros, ler_filtros, renderizar_filtros
from components.graficos import (
    grafico_frequencia,
    grafico_resposta_pronta,
    grafico_uso_autonomia,
)
from components.metricas import aplicar_estilo, renderizar_kpis
from components.secoes import (
    aviso_retrato,
    secao_conclusao,
    secao_hipotese,
    secao_verificacao,
)
from config.google_sheets import carregar_planilha

st.set_page_config(page_title="IA e Autonomia nos Estudos", layout="wide")
aplicar_estilo()


def mostrar_grafico(fig, aviso: str) -> None:
    """Mostra o gráfico ou, se não houver dados, uma mensagem informativa."""
    if fig is None:
        st.info(aviso)
    else:
        st.plotly_chart(fig)


@st.cache_data(ttl=60, show_spinner=False)
def carregar_base():
    """Lê a planilha, limpa e guarda em cache por 60 s (evita requisições
    desnecessárias). Devolve (base limpa, relatório, horário da leitura)."""
    bruto = carregar_planilha()
    df, rel = limpar(bruto)
    return df, rel, datetime.now().strftime("%H:%M:%S")


def _atualizar_agora() -> None:
    """Botão manual: descarta o cache para forçar nova leitura."""
    st.cache_data.clear()


def secao_graficos(base) -> None:
    """Seções 5 e 6: gráficos (usam a base já filtrada)."""
    escala = st.radio(
        "Escala dos gráficos de cruzamento",
        ["Contagem", "Percentual"], horizontal=True, key="escala_graficos",
    )
    percentual = escala == "Percentual"

    col_a, col_b = st.columns(2)
    with col_a:
        mostrar_grafico(grafico_frequencia(base), "Sem dados de frequência de uso.")
    with col_b:
        mostrar_grafico(
            grafico_uso_autonomia(base, percentual),
            "Sem respostas de autonomia para este filtro.",
        )
    mostrar_grafico(
        grafico_resposta_pronta(base, percentual),
        "Sem respostas sobre respostas prontas para este filtro.",
    )
    st.caption(
        "Atenção: os grupos são pequenos (veja o n no eixo de cada barra). "
        "Percentuais de grupos com poucas pessoas exageram diferenças; "
        "use a escala 'Contagem' como referência."
    )


# 1-3. Cabeçalho, pergunta de pesquisa e hipótese (conteúdo fixo)
st.title("Inteligência Artificial e Autonomia nos Estudos")
st.markdown(
    "**Pergunta de pesquisa:** Estudantes que utilizam inteligência artificial "
    "com maior frequência apresentam menor autonomia para resolver atividades escolares?"
)
st.markdown(
    "**Hipótese inicial:** Estudantes que utilizam IA frequentemente tendem a "
    "apresentar menor autonomia na resolução de atividades escolares, recorrendo "
    "mais às ferramentas para obter respostas prontas."
)


@st.fragment(run_every=60)
def painel() -> None:
    """Parte dinâmica: reexecuta sozinha a cada 60 s sem recarregar a página
    inteira, e os filtros (session_state) continuam como estavam."""
    topo, botao = st.columns([5, 1.5], vertical_alignment="center")
    try:
        df, rel, horario = carregar_base()
    except Exception as erro:  # conexão, permissão, planilha fora do ar...
        topo.error(
            f"Não foi possível carregar os dados ({type(erro).__name__}). "
            "Verifique a conexão e as permissões da planilha."
        )
        botao.button("Tentar novamente", on_click=_atualizar_agora)
        return
    topo.caption(
        f"Última leitura da planilha: {horario} · atualização automática a cada 60 s"
    )
    botao.button("Atualizar dados", on_click=_atualizar_agora)

    if df.empty:
        st.info("Ainda não há respostas válidas para exibir.")
        return

    uso, autonomia = ler_filtros()
    base = aplicar_filtros(df, uso, autonomia)

    # 4. Indicadores principais (refletem os filtros)
    st.subheader("Indicadores principais")
    st.caption(f"Base analisada: {len(base)} de {len(df)} participantes válidos.")
    if base.empty:
        st.warning("Nenhum participante atende aos filtros escolhidos.")
    else:
        renderizar_kpis(indicadores(base))

    # 7. Filtros (no topo da área de gráficos)
    st.subheader("Análise por grupo")
    renderizar_filtros()

    # 5-6. Gráficos
    if not base.empty:
        secao_graficos(base)

    # 8-10. Conclusão, verificação crítica e relação com a hipótese
    st.divider()
    aviso_retrato(len(df))
    secao_conclusao()
    secao_verificacao()
    secao_hipotese(df)


painel()