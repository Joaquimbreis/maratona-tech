"""Limpeza e padronização dos dados da pesquisa (sem dependência do Streamlit).

Uso isolado (da raiz do projeto, com o .venv ativo):
    python -m analysis.limpeza caminho/para/respostas.xlsx
"""
import sys

import pandas as pd

# ----------------------------------------------------------------------
# Registros que NÃO são respostas reais (documentado no relatório).
# Formato: "AAAA-MM-DD HH:MM:SS" (carimbo de data/hora da planilha).
# ----------------------------------------------------------------------
TESTES = ["2026-10-30 23:03:03"]  # resposta de teste feita pelo autor

# Mapeamento: trecho do cabeçalho original -> nome curto da coluna.
# Usa o TEXTO da pergunta (não o número), pois o Forms numera o
# consentimento como "Pergunta 1".
COLUNAS = {
    "Carimbo": "timestamp",
    "Consentimento": "consentimento",
    "Frequência de utilização": "freq_uso_ia",
    "Autonomia na resolução": "primeira_acao",
    "Dependência de respostas": "resposta_pronta",
    "Percepção de autonomia": "autonomia_percebida",
    "Finalidade de utilização": "finalidade",
    "Verificação do aprendizado": "compreensao",
}

# Alternativas válidas, em ordem (mesmo texto do formulário, sem ponto final).
ESCALA_FREQ = ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"]
ORDEM = {
    "freq_uso_ia": ESCALA_FREQ,
    "resposta_pronta": ESCALA_FREQ,
    "compreensao": ESCALA_FREQ,
    # Da MAIOR para a MENOR autonomia percebida.
    "autonomia_percebida": [
        "Sim, com facilidade",
        "Sim, mas tenho algumas dificuldades",
        "Depende da atividade",  # categoria neutra (decisão documentada)
        "Tenho bastante dificuldade",
        "Não consigo realizar a maioria das atividades sem IA",
    ],
    "primeira_acao": [
        "Tento resolver sozinho antes de procurar ajuda",
        "Consulto materiais didáticos ou pesquisas na internet",
        "Peço ajuda a professores ou colegas",
        "Consulto uma ferramenta de Inteligência Artificial",
        "Peço diretamente a resposta à Inteligência Artificial",
    ],
    "finalidade": [
        "Tirar dúvidas e compreender conteúdos",
        "Resolver exercícios e atividades",
        "Elaborar resumos e organizar informações",
        "Pesquisar assuntos e encontrar informações",
        "Produzir textos e trabalhos escolares",
        "Não utilizo Inteligência Artificial nos estudos",
        "Outros",
    ],
}
CONSENTIMENTO_OK = "Sim, concordo"

# Agrupamento usado nos cruzamentos (n pequeno => poucas categorias).
GRUPO_USO = {
    "Nunca": "Nunca/Raramente", "Raramente": "Nunca/Raramente",
    "Às vezes": "Às vezes",
    "Frequentemente": "Frequentemente/Sempre", "Sempre": "Frequentemente/Sempre",
}
ORDEM_GRUPO = ["Nunca/Raramente", "Às vezes", "Frequentemente/Sempre"]


def renomear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os cabeçalhos longos do Forms pelos nomes curtos."""
    novos = {}
    for col in df.columns:
        for trecho, nome in COLUNAS.items():
            if trecho.lower() in str(col).lower():
                novos[col] = nome
                break
    df = df.rename(columns=novos)
    faltando = [n for n in COLUNAS.values() if n not in df.columns]
    if faltando:
        raise ValueError(f"Colunas não encontradas na planilha: {faltando}")
    return df[list(COLUNAS.values())]


def _padronizar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espaços e ponto final; vazio vira NaN. Não altera o conteúdo."""
    for col in df.columns.drop("timestamp"):
        s = df[col].astype("string").str.strip().str.rstrip(".").str.strip()
        df[col] = s.replace("", pd.NA)
    return df


def limpar(df_bruto: pd.DataFrame):
    """Recebe o DataFrame bruto e devolve (df_limpo, relatorio).

    O DataFrame de entrada NÃO é modificado (a cópia original é preservada).
    Nada é inventado ou preenchido: brancos continuam brancos.
    """
    rel = {"inicial": len(df_bruto), "removidos": [], "problemas": []}
    df = renomear_colunas(df_bruto.copy())
    df["timestamp"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = _padronizar_texto(df)

    def remover(mascara, motivo):
        n = int(mascara.sum())
        if n:
            rel["removidos"].append({"motivo": motivo, "quantidade": n})
        return df[~mascara]

    # 1) Respostas de teste
    chave = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df = remover(chave.isin(TESTES), "Resposta de teste do autor")

    # 2) Sem consentimento (ou consentimento ausente)
    df = remover(df["consentimento"] != CONSENTIMENTO_OK, "Sem consentimento")

    # 3) Duplicatas exatas (mesmo carimbo e mesmas respostas)
    df = remover(df.duplicated(keep="first"), "Registro duplicado")

    # Aviso (não remove): respostas idênticas em carimbos diferentes
    # podem ser pessoas diferentes, então só informamos.
    idem = int(df.drop(columns="timestamp").duplicated(keep=False).sum())
    if idem:
        rel["problemas"].append(
            f"{idem} registros com respostas idênticas a outro (mantidos)."
        )

    # 4) Valores fora das alternativas oficiais (relatar; não corrigir)
    for col, validos in ORDEM.items():
        invalidos = df[col].notna() & ~df[col].isin(validos)
        if invalidos.any():
            rel["problemas"].append(
                f"{int(invalidos.sum())} valor(es) inválido(s) em '{col}' (mantidos)."
            )

    # 5) Brancos (mantidos; cada indicador usa seu próprio denominador)
    brancos = df[list(ORDEM)].isna().sum()
    for col, n in brancos[brancos > 0].items():
        rel["problemas"].append(f"{int(n)} resposta(s) em branco em '{col}'.")

    # 6) Inconsistência: "Nunca" usa IA, mas responde como se usasse
    nunca = df["freq_uso_ia"] == "Nunca"
    df["inconsistente"] = nunca & (
        df["resposta_pronta"].isin(ESCALA_FREQ[1:]) | df["compreensao"].notna()
    )
    n_inc = int(df["inconsistente"].sum())
    if n_inc:
        rel["problemas"].append(
            f"{n_inc} participante(s) com uso 'Nunca' mas respostas sobre uso "
            "de IA (sinalizados em 'inconsistente'; mantidos)."
        )

    # Colunas auxiliares: categorias ordenadas, códigos e grupo
    for col, ordem in ORDEM.items():
        df[col] = pd.Categorical(df[col], categories=ordem, ordered=True)
    for col in ["freq_uso_ia", "resposta_pronta", "compreensao", "autonomia_percebida"]:
        df[col + "_cod"] = df[col].cat.codes.where(df[col].notna())
    # autonomia_cod: 0 = "com facilidade" ... 4 = "não consigo"; inverter para
    # que valores MAIORES signifiquem MAIOR autonomia:
    df["autonomia_cod"] = 4 - df["autonomia_percebida_cod"]
    df = df.drop(columns="autonomia_percebida_cod")
    df["grupo_uso"] = pd.Categorical(
        df["freq_uso_ia"].map(GRUPO_USO), categories=ORDEM_GRUPO, ordered=True
    )

    df = df.reset_index(drop=True)
    rel["final"] = len(df)
    return df, rel


def imprimir_relatorio(rel: dict) -> None:
    """Mostra o relatório de limpeza no terminal."""
    print(f"Registros iniciais: {rel['inicial']}")
    for r in rel["removidos"]:
        print(f"  Removidos: {r['quantidade']} ({r['motivo']})")
    print(f"Respostas válidas: {rel['final']}")
    for p in rel["problemas"]:
        print(f"  Atenção: {p}")


if __name__ == "__main__":
    caminho = sys.argv[1]
    bruto = pd.read_excel(caminho) if caminho.endswith(".xlsx") else pd.read_csv(caminho)
    limpo, relatorio = limpar(bruto)
    imprimir_relatorio(relatorio)
    print()
    print(limpo["freq_uso_ia"].value_counts().sort_index().to_string())
    print(limpo["grupo_uso"].value_counts().sort_index().to_string())