"""Diagnóstico do secrets.toml sem expor valores."""
import tomllib
from google.oauth2.service_account import Credentials

with open(".streamlit/secrets.toml", "rb") as f:
    d = tomllib.load(f)

sa = d.get("gcp_service_account", {})
obrigatorios = ["type", "project_id", "private_key_id", "private_key",
                "client_email", "token_uri"]
print("Campos faltando:", [c for c in obrigatorios if not sa.get(c)])

pk = sa.get("private_key", "")
print("Começa certo:", pk.startswith("-----BEGIN PRIVATE KEY-----"))
print("Termina certo:", pk.strip().endswith("-----END PRIVATE KEY-----"))
print("Quebras de linha reais:", pk.count("\n"))
print("Tem \\n literal (errado):", "\\n" in pk)
print("Tamanho da chave:", len(pk))
print("ID da planilha preenchido:", bool(d.get("sheets", {}).get("spreadsheet_id")))

try:
    Credentials.from_service_account_info(
        sa, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    print("Credenciais: OK")
except Exception as e:
    print("Credenciais: ERRO ->", type(e).__name__, str(e)[:150])