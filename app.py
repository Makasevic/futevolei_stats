import streamlit as st
import plotly.express as px
from data_processing import filtrar_por_periodo, calcular_estatisticas, preparar_matriz_saldos, preparar_matriz_parcerias
from api import get_pages, extrair_dados
import pandas as pd

# Carregar dados
pages = get_pages()
data = [extrair_dados(page) for page in pages]
df = pd.DataFrame(data, columns=["winner1", "winner2", "loser1", "loser2", "date"]).set_index("date")
df["dupla_winner"] = df.apply(lambda row: " e ".join(sorted([row["winner1"], row["winner2"]])), axis=1)
df["dupla_loser"] = df.apply(lambda row: " e ".join(sorted([row["loser1"], row["loser2"]])), axis=1)

# Interface
tab1, tab2, tab3 = st.tabs(["Jogadores", "Duplas", "Confrontos"])
periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]

with tab1:
    st.title("Jogadores")
    periodo = st.radio("Período:", periodos)
    df_filtrado = filtrar_por_periodo(df, periodo)
    estatisticas = calcular_estatisticas(df_filtrado, "jogadores")
    st.dataframe(estatisticas)

with tab2:
    st.title("Duplas")
    periodo = st.radio("Período:", periodos)
    df_filtrado = filtrar_por_periodo(df, periodo)
    estatisticas = calcular_estatisticas(df_filtrado, "duplas")
    st.dataframe(estatisticas)

with tab3:
    st.title("Confrontos")
    matriz = preparar_matriz_saldos(df, "jogadores")
    st.dataframe(matriz)

