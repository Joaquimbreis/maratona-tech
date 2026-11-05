"""Seções textuais finais: conclusão, verificação crítica e relação com a
hipótese.

O TEXTO fica em arquivos na pasta conteudo/ (e não dentro do código), e só
é escrito depois de congelar a base e analisar com o Gemini. Enquanto estiver
pendente, o dashboard mostra um aviso em vez de inventar conclusões.
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from analysis.comparacao import comparacao_grupos
from analysis.exploracao import testes

PASTA = Path(__file__).resolve().parent.parent / "conteudo"


def _ler_texto(nome: str):
    """Devolve o texto do arquivo, ou None se faltar ou estiver PENDENTE."""
    caminho = PASTA / nome
    if not caminho.exists():
        return None
    texto = caminho.read_text(encoding="utf-8-sig").strip()
    if not texto or texto.upper().startswith("PENDENTE"):
        return None
    return texto


def _ler_json(nome: str, padrao):
    """Devolve (dados, erro). Em caso de arquivo ausente ou inválido, usa o padrão."""
    caminho = PASTA / nome
    try:
        return json.loads(caminho.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return padrao, None
    except json.JSONDecodeError as e:
        return padrao, f"{nome} está com formato inválido (linha {e.lineno})."


def aviso_retrato(n_atual: int) -> None:
    """Avisa se a base mudou desde que os textos foram escritos."""
    retrato, erro = _ler_json("retrato.json", {})
    if erro:
        st.error(erro)
        return
    n, data = retrato.get("n"), retrato.get("data")
    if n is None:
        st.info("Os textos destas seções serão escritos sobre a base final, que ainda não foi registrada.")
    elif n != n_atual:
        st.warning(
            f"Os textos foram escritos com {n} respostas válidas ({data}). "
            f"A base atual tem {n_atual}; números citados nos textos podem estar desatualizados."
        )
    else:
        st.caption(f"Textos baseados em {n} respostas válidas, registradas em {data}.")


def secao_conclusao() -> None:
    """Seção 8: conclusão da investigação."""
    st.subheader("Conclusão da investigação")
    texto = _ler_texto("conclusao.md")
    if texto:
        st.markdown(texto)
    else:
        st.info("Conclusão pendente: será escrita após a análise da base final.")


def secao_verificacao() -> None:
    """Seção 9: verificação crítica das sugestões do Gemini."""
    st.subheader("Verificação crítica da IA")
    itens, erro = _ler_json("verificacao_gemini.json", [])
    if erro:
        st.error(erro)
        return
    if not itens:
        st.info("Verificação pendente: será feita comparando a análise do Gemini com os dados reais.")
        return
    contagem = Counter(i.get("classificacao", "Sem classificação") for i in itens)
    st.caption(" · ".join(f"{k}: {v}" for k, v in contagem.items()))
    for item in itens:
        sugestao = item.get("sugestao_gemini", "")
        resumo = sugestao if len(sugestao) <= 90 else sugestao[:87] + "..."
        with st.expander(f"{item.get('classificacao', '?')}: {resumo}"):
            st.markdown(f"**Sugestão original do Gemini:** {sugestao}")
            st.markdown(f"**Nossa avaliação:** {item.get('nossa_avaliacao', '')}")
            st.markdown(f"**Evidência nos dados:** {item.get('evidencia', '')}")


def secao_hipotese(df: pd.DataFrame) -> None:
    """Seção 10: relação com a hipótese (texto + números sempre atualizados)."""
    st.subheader("Relação com a hipótese")
    texto = _ler_texto("hipotese.md")
    if texto:
        st.markdown(texto)
    else:
        st.info("Texto pendente: será escrito após a análise da base final.")

    st.markdown("**Comparação entre grupos de uso** (base completa, calculada automaticamente)")
    st.dataframe(comparacao_grupos(df))

    with st.expander("Testes de associação (Spearman, exploratórios)"):
        st.markdown("Todos os participantes válidos:")
        st.dataframe(testes(df), hide_index=True)
        st.markdown("Sem os participantes que marcaram 'Nunca' mas responderam sobre uso (sensibilidade):")
        st.dataframe(testes(df, excluir_inconsistentes=True), hide_index=True)
        st.caption(
            "Em 'autonomia', valores maiores = mais autonomia. Com n pequeno e vários "
            "testes, p-valores devem ser lidos com cautela; correlação não indica causa."
        )