import streamlit as st
import pandas as pd
import plotly.express as px

# Dados da tabela
data = {
    "jogadores": ["Benchi", "Bruno", "Diego", "Gustavo", "JC", "Marcelo", "Renato"],
    "vitórias": [4, 2, 4, 1, 1, 1, 1],
    "derrotas": [1, 1, 3, 2, 1, 2, 0],
    "aproveitamento": [80.0, 66.67, 57.14, 33.33, 50.0, 33.33, 100.0]
}

df = pd.DataFrame(data)

# Título do app
st.title("Análise de Desempenho dos Jogadores")

# Mostra a tabela
st.subheader("Tabela de Desempenho")
st.dataframe(df)

# Gráfico de barras vermelhas (vitórias)
st.subheader("Gráfico de Vitórias")
fig_vitorias = px.bar(df, x="jogadores", y="vitórias", title="Vitórias por Jogador",
                      labels={"vitórias": "Vitórias", "jogadores": "Jogadores"},
                      color_discrete_sequence=["red"])
st.plotly_chart(fig_vitorias)

# Gráfico de barras azuis (derrotas)
st.subheader("Gráfico de Derrotas")
fig_derrotas = px.bar(df, x="jogadores", y="derrotas", title="Derrotas por Jogador",
                      labels={"derrotas": "Derrotas", "jogadores": "Jogadores"},
                      color_discrete_sequence=["blue"])
st.plotly_chart(fig_derrotas)

# Gráfico de linha (aproveitamento)
st.subheader("Gráfico de Aproveitamento")
fig_aproveitamento = px.line(df, x="jogadores", y="aproveitamento", title="Aproveitamento por Jogador",
                             labels={"aproveitamento": "Aproveitamento (%)", "jogadores": "Jogadores"},
                             markers=True)
st.plotly_chart(fig_aproveitamento)
