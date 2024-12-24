import streamlit as st
import pandas as pd
import plotly.express as px

# Título do app
st.title("Exemplo de Gráfico no Streamlit")

# Criando um DataFrame de exemplo
data = {
    "Categoria": ["A", "B", "C", "D"],
    "Valor": [10, 20, 30, 40]
}
df = pd.DataFrame(data)

# Exibindo o DataFrame
st.subheader("Tabela de Dados")
st.dataframe(df)

# Criando um gráfico de barras
st.subheader("Gráfico Interativo")
fig = px.bar(df, x="Categoria", y="Valor", title="Gráfico de Barras")
st.plotly_chart(fig)

# Entrada interativa
st.subheader("Personalize o gráfico")
incremento = st.slider("Adicione um valor a cada barra", min_value=0, max_value=20, step=1)
df["Valor Incrementado"] = df["Valor"] + incremento

fig2 = px.bar(df, x="Categoria", y="Valor Incrementado", title="Gráfico Incrementado")
st.plotly_chart(fig2)
