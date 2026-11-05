"""Integração com o Google Planilhas (somente leitura)."""
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _cliente() -> gspread.Client:
    """Autentica com a conta de serviço guardada em st.secrets."""
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds)


def carregar_planilha() -> pd.DataFrame:
    """Lê a primeira aba da planilha e devolve um DataFrame bruto."""
    planilha = _cliente().open_by_key(st.secrets["sheets"]["spreadsheet_id"])
    registros = planilha.sheet1.get_all_records()
    return pd.DataFrame(registros)