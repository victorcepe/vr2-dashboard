import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

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

# --- Consulta os dados da tabela miner_status ---
conn = create_connection()
if conn is None:
    st.stop()

query = "SELECT * FROM vr2miner.miner_status ORDER BY location, id"
df = pd.read_sql(query, conn)
original_df = df
conn.close()

# --- Exibe os dados agrupados por localização ---
if df.empty:
    st.write("Nenhum dado para exibir!")
else:
    # Agrupa o dataframe por 'location' e, em cada grupo, remove as colunas "id" e "location"
    groups = {}
    for loc, group in df.groupby("location"):
        group_display = group.drop(columns=["id", "location"]).reset_index(drop=True)
        group_display.index = group_display.index + 1  # inicia o índice em 1
        groups[loc] = group_display

    # Exibe cada grupo em um expander separado
    for loc, group_df in groups.items():
        with st.expander(f"📍 {loc}", expanded=True):
            st.dataframe(group_df)
