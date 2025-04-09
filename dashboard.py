import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os
from dotenv import load_dotenv
import re
import pytz
from pytz import timezone

# Carrega as variáveis de ambiente
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Local Timezone
tz = timezone("America/Sao_Paulo")
now = datetime.now(tz)

# --- Configurações iniciais do Streamlit ---
st.set_page_config(page_title="VR2 Miners Dashboard", layout="wide")
st.title("🔧 VR2 Miners Dashboard - Status")

# --- Função para conectar ao MySQL ---
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("host_name"),
            user=os.environ.get("user_name"),
            passwd=os.environ.get("user_password"),
            database=os.environ.get("db_name")
        )
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
    return connection

# --- Função para formatar o status ativo com ícones ---
def format_active_status(row):
    if row["active"] == "No":
        return "🔴 No"
    elif row["active"] == "Yes" and pd.to_datetime(row["updated_at"]).tz_localize(tz) < now - timedelta(hours=1):
        return "🟡 Yes (Check)"
    else:
        return "🟢 Yes"

# --- Consulta os dados da tabela miner_status ---
conn = create_connection()
if conn is None:
    st.stop()

query = "SELECT * FROM vr2miner.miner_status ORDER BY location, name"
df = pd.read_sql(query, conn)
conn.close()

# --- Processamento de dados ---
df["updated_at_raw"] = pd.to_datetime(df["updated_at"])  # usado para lógica
df["updated_at"] = df["updated_at_raw"].dt.strftime('%d/%m/%Y %H:%M:%S')  # exibido formatado

df['preset_valor'] = df['preset'].apply(lambda x: float(re.findall(r'\d+(?:\.\d+)?', x)[0]) if isinstance(x, str) and re.findall(r'\d+(?:\.\d+)?', x) else 0)
df["active"] = df.apply(format_active_status, axis=1)

# --- Métricas globais ---
ativas = df[df["active"].str.contains("🟢")].shape[0]
inativas = df[df["active"].str.contains("🔴")].shape[0]
total_th = df['preset_valor'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("🔋 Active Miners", ativas)
col2.metric("🔌 Inactive Miners", inativas)
col3.metric("💪 TH Sum (preset)", f"{total_th:.2f} TH")
st.divider()

# --- Exibe os dados agrupados por localização ---
if df.empty:
    st.write("No data!")
else:
    groups = {}
    for loc, group in df.groupby("location"):
        group_display = group.drop(columns=["id", "location", "preset_valor", "updated_at_raw"]).reset_index(drop=True)
        group_display.index = group_display.index + 1  # inicia o índice em 1
        groups[loc] = group_display

    for loc, group_df in groups.items():
        with st.expander(f"📍 {loc}", expanded=True):
            st.dataframe(group_df)

# Comando para rodar:
# python -m streamlit run D:\Miners\vr2-dashboard\dashboard.py
