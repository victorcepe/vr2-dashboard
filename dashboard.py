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

# Carrega as variáveis de ambiente
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

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
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
    updated_at = row["updated_at_raw"]

    if updated_at.tzinfo is None:
        updated_at = updated_at.tz_localize("UTC").astimezone(pytz.timezone("America/Sao_Paulo"))
    else:
        updated_at = updated_at.astimezone(pytz.timezone("America/Sao_Paulo"))

    if row["active"] == "No":
        return "🔴 No"
    elif (updated_at < now - timedelta(hours=1)) or (row["active"] == "Yes" and row["status"] != "mining"):
        return "🟡 Yes (Check)"
    else:
        return "🟢 Yes"

# --- Função para formatar a temperatura ---
def format_temperature(temp):
    if temp == 0:
        return '-'
    elif temp < 75:
        return f"❄️ {temp}°C"
    elif temp >= 78:
        return f"🔥 {temp}°C"
    else:
        return f"🌡️ {temp}°C"

# --- Consulta os dados da tabela miner_status ---
conn = create_connection()
if conn is None:
    st.stop()

query = "SELECT * FROM vr2miner.miner_status ORDER BY location, name"
df = pd.read_sql(query, conn)
conn.close()

# --- Processamento de dados ---
# Converte com timezone direto
df["updated_at_raw"] = pd.to_datetime(df["updated_at"]).dt.tz_localize("America/Sao_Paulo")
df["updated_at"] = df["updated_at_raw"].dt.strftime('%d/%m/%Y %H:%M:%S')  # só para exibição

# Lógica de presets e temperatura
df['preset_valor'] = df['preset'].apply(lambda x: float(re.findall(r'\d+(?:\.\d+)?', x)[0]) if isinstance(x, str) and re.findall(r'\d+(?:\.\d+)?', x) else 0)
df["active"] = df.apply(format_active_status, axis=1)
df["temperature"] = df["temperature"].apply(format_temperature)

# --- Métricas globais ---
mineradores_ativos = df["active"].str.contains("🟢|🟡")
mineradores_inativos = df["active"].str.contains("🔴")

ativas = df[mineradores_ativos].shape[0]
inativas = df[mineradores_inativos].shape[0]
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
