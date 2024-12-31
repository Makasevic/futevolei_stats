# visuals.py

import streamlit as st
import plotly.express as px

def exibir_graficos(df, eixo_x, titulo):
    """
    Exibe gráficos de vitórias, derrotas e aproveitamento em abas separadas.
    """
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(
        df,
        x=eixo_x,
        y="vitórias",
        title=f"Vitórias por {titulo}",
        color_discrete_sequence=["steelblue"],
    )
    fig_vitorias.update_xaxes(title="")  # Remove a label do eixo x
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(
        df,
        x=eixo_x,
        y="derrotas",
        title=f"Derrotas por {titulo}",
        color_discrete_sequence=["indianred"],
    )
    fig_derrotas.update_xaxes(title="")
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(
        df,
        x=eixo_x,
        y="aproveitamento",
        title=f"Aproveitamento por {titulo}",
        markers=True,
        text="aproveitamento",
    )
    fig_aproveitamento.update_traces(textposition="top center", textfont_size=12)
    fig_aproveitamento.update_xaxes(title="")
    st.plotly_chart(fig_aproveitamento, use_container_width=True, config={"staticPlot": True})
