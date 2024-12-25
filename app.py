import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests


# Configuração da API do Notion
NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


# Funções auxiliares
def filtrar_por_periodo(df, periodo):
    """Filtra o DataFrame de acordo com o período selecionado."""
    if periodo == "1 semana":
        data_inicio = datetime.now() - timedelta(weeks=1)
    elif periodo == "1 mês":
        data_inicio = datetime.now() - timedelta(weeks=4)
    elif periodo == "3 meses":
        data_inicio = datetime.now() - timedelta(weeks=12)
    elif periodo == "6 meses":
        data_inicio = datetime.now() - timedelta(weeks=26)
    elif periodo == "1 ano":
        data_inicio = datetime.now() - timedelta(weeks=52)
    else:  # "Todos os dados"
        return df

    return df[df.index >= data_inicio.date()]


def preparar_dados_individuais(df):
    """Prepara dados de vitórias, derrotas e aproveitamento para jogadores."""
    jogador_w = pd.DataFrame(df.iloc[:, 0:2].values.reshape(-1)).value_counts()
    jogador_l = pd.DataFrame(df.iloc[:, 2:4].values.reshape(-1)).value_counts()

    jogadores_list = sorted(set(jogador_w.index) | set(jogador_l.index))
    jogador_w = jogador_w.reindex(jogadores_list, fill_value=0)
    jogador_l = jogador_l.reindex(jogadores_list, fill_value=0)

    jogador_w_pct = jogador_w / (jogador_w + jogador_l) * 100
    jogadores = pd.concat([jogador_w, jogador_l, jogador_w_pct], axis=1).reset_index()
    jogadores.columns = ["jogadores", "vitórias", "derrotas", "aproveitamento"]
    jogadores["vitórias"] = jogadores["vitórias"].astype(int)
    jogadores["derrotas"] = jogadores["derrotas"].astype(int)

    return jogadores


def preparar_dados_duplas(df):
    """Prepara dados de vitórias, derrotas e aproveitamento para duplas."""
    duplas_w = pd.Series([f"{x} e {y}" for x, y in df.iloc[:, 0:2].values]).value_counts()
    duplas_l = pd.Series([f"{x} e {y}" for x, y in df.iloc[:, 2:4].values]).value_counts()

    duplas_list = sorted(set(duplas_w.index) | set(duplas_l.index))
    duplas_w = duplas_w.reindex(duplas_list, fill_value=0)
    duplas_l = duplas_l.reindex(duplas_list, fill_value=0)

    duplas_w_pct = duplas_w / (duplas_w + duplas_l) * 100
    duplas = pd.concat([duplas_w, duplas_l, duplas_w_pct], axis=1).reset_index()
    duplas.columns = ["duplas", "vitórias", "derrotas", "aproveitamento"]
    duplas["vitórias"] = duplas["vitórias"].astype(int)
    duplas["derrotas"] = duplas["derrotas"].astype(int)

    return duplas


def exibir_graficos(df, eixo_x, titulo):
    """Exibe gráficos de vitórias, derrotas e aproveitamento."""
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(df, x=eixo_x, y="vitórias", title=f"Vitórias por {titulo}",
                          color_discrete_sequence=["red"])
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(df, x=eixo_x, y="derrotas", title=f"Derrotas por {titulo}",
                          color_discrete_sequence=["blue"])
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(df, x=eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}",
                                 markers=True)
    st.plotly_chart(fig_aproveitamento, use_container_width=True, config={"staticPlot": True})


# Simulação de dados para exemplo
data = {
    "winner1": ["Benchi", "Gustavo", "Marcelo", "Diego", "Renato"],
    "winner2": ["Marcelo", "Diego", "Renato", "Gustavo", "Benchi"],
    "loser1": ["Diego", "Renato", "Gustavo", "Marcelo", "JC"],
    "loser2": ["JC", "Marcelo", "Diego", "Benchi", "Gustavo"],
    "date": [
        (datetime.now() - timedelta(days=i)).date() for i in range(10, 15)
    ]
}
df = pd.DataFrame(data).set_index("date")

# Ordenar vencedores e perdedores
df[["winner1", "winner2"]] = df[["winner1", "winner2"]].apply(lambda x: sorted(x), axis=1)
df[["loser1", "loser2"]] = df[["loser1", "loser2"]].apply(lambda x: sorted(x), axis=1)

# Interface Streamlit
tab1, tab2, tab3 = st.tabs(["Jogadores", "Duplas", "Jogos"])

# Adicionar seleção de período em cada aba
periodos = ["1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]

with tab1:
    st.title("Análise de Desempenho dos Jogadores")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    jogadores = preparar_dados_individuais(df_filtrado)
    exibir_graficos(jogadores, "jogadores", "Jogador")
    st.dataframe(jogadores.set_index("jogadores"))

with tab2:
    st.title("Análise de Desempenho das Duplas")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    duplas = preparar_dados_duplas(df_filtrado)
    exibir_graficos(duplas, "duplas", "Dupla")
    st.dataframe(duplas.set_index("duplas"))

with tab3:
    st.title("Jogos Registrados")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    st.dataframe(df_filtrado)
