import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

def extrair_dados(page_data):
    winners = []
    dupla1 = page_data['properties'].get('Dupla 1')
    if dupla1 and dupla1.get('type') == 'multi_select':
        for item in dupla1.get('multi_select', []):
            if 'name' in item:
                winners.append(item['name'])
    losers = []
    dupla2 = page_data['properties'].get('Dupla 2')
    if dupla2 and dupla2.get('type') == 'multi_select':
        for item in dupla2.get('multi_select', []):
            if 'name' in item:
                losers.append(item['name'])
    submission_date = None
    submission_prop = page_data['properties'].get('Submission time')
    if submission_prop and submission_prop.get('type') == 'created_time':
        submission_date = submission_prop.get('created_time')
        submission_date = [datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date()]
    return winners+losers+submission_date

def get_pages(num_pages=None):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages
    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

pages = get_pages()

df = []
for page in pages:
    df.append(extrair_dados(page))
df = pd.DataFrame(df)
df.columns = ['winner1','winner2','loser1','loser2','date']
df = df.set_index('date')

for i in range(df.shape[0]):
    df.iloc[i, 0:2] = df.iloc[i, 0:2].sort_values()
    df.iloc[i, 2:4] = df.iloc[i, 2:4].sort_values()

# Abas
tab1, tab2 = st.tabs(["Jogadores", "Duplas"])

jogador_w = pd.DataFrame(df.iloc[:, 0:2].values.reshape(-1))
jogador_w = jogador_w.value_counts()

jogador_l = pd.DataFrame(df.iloc[:, 2:4].values.reshape(-1))
jogador_l = jogador_l.value_counts()

jogadores_list = sorted(set(list(jogador_w.index) + list(jogador_l.index)))
jogador_w = jogador_w.reindex(index=jogadores_list).fillna(0)
jogador_l = jogador_l.reindex(index=jogadores_list).fillna(0)

jogador_w_pct = jogador_w / (jogador_w + jogador_l) * 100
jogadores = pd.concat([jogador_w, jogador_l, jogador_w_pct], axis=1)
jogadores = jogadores.rename_axis("jogadores")
jogadores.columns = ['vitórias','derrotas','aproveitamento']
jogadores = jogadores.reset_index()
jogadores['vitórias'] = jogadores['vitórias'].astype(int)
jogadores['derrotas'] = jogadores['derrotas'].astype(int)
jogadores = jogadores.set_index('jogadores')
jogadores = jogadores[~jogadores.index.str.contains("Outro")]

# Título do app
st.title("Análise de Desempenho dos Jogadores")

with tab1:
    # Gráfico de barras vermelhas (vitórias)
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(jogadores, x="jogadores", y="vitórias", title="Vitórias por Jogador",
                          labels={"vitórias": "Vitórias", "jogadores": "Jogadores"},
                          color_discrete_sequence=["red"])
    st.plotly_chart(fig_vitorias)

    # Gráfico de barras azuis (derrotas)
    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(jogadores, x="jogadores", y="derrotas", title="Derrotas por Jogador",
                          labels={"derrotas": "Derrotas", "jogadores": "Jogadores"},
                          color_discrete_sequence=["blue"])
    st.plotly_chart(fig_derrotas)

    # Gráfico de linha (aproveitamento)
    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(jogadores, x="jogadores", y="aproveitamento", title="Aproveitamento por Jogador",
                                 labels={"aproveitamento": "Aproveitamento (%)", "jogadores": "Jogadores"},
                                 markers=True)
    st.plotly_chart(fig_aproveitamento)

    # Mostra a tabela
    st.subheader("Tabela de Desempenho")
    st.dataframe(jogadores)


duplas_w = [x + " e " + y for x, y in df.iloc[:, 0:2].values]
duplas_w = pd.DataFrame(duplas_w)
duplas_w = duplas_w.value_counts()

duplas_l = [x + " e " + y for x, y in df.iloc[:, 2:4].values]
duplas_l = pd.DataFrame(duplas_l)
duplas_l = duplas_l.value_counts()

duplas = sorted(set(list(duplas_w.index) + list(duplas_l.index)))
duplas_w = duplas_w.reindex(index=duplas).fillna(0)
duplas_l = duplas_l.reindex(index=duplas).fillna(0)

duplas_w_pct = duplas_w / (duplas_w + duplas_l) * 100
duplas = pd.concat([duplas_w, duplas_l, duplas_w_pct], axis=1)
duplas = duplas.rename_axis("duplas")
duplas.columns = ['vitórias','derrotas','aproveitamento']
duplas = duplas.reset_index()
duplas['vitórias'] = duplas['vitórias'].astype(int)
duplas['derrotas'] = duplas['derrotas'].astype(int)
duplas = duplas.set_index('duplas')
duplas = duplas[~duplas.index.str.contains("Outro")]


with tab2:
    # Gráfico de barras vermelhas (vitórias)
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(duplas.reset_index(), x="duplas", y="vitórias", title="Vitórias por Dupla",
                          labels={"vitórias": "Vitórias", "duplas": "Duplas"},
                          color_discrete_sequence=["red"])
    st.plotly_chart(fig_vitorias)

    # Gráfico de barras azuis (derrotas)
    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(duplas.reset_index(), x="duplas", y="derrotas", title="Derrotas por Dupla",
                          labels={"derrotas": "Derrotas", "duplas": "Duplas"},
                          color_discrete_sequence=["blue"])
    st.plotly_chart(fig_derrotas)

    # Gráfico de linha (aproveitamento)
    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(duplas.reset_index(), x="duplas", y="aproveitamento", title="Aproveitamento por Dupla",
                                 labels={"aproveitamento": "Aproveitamento (%)", "duplas": "Duplas"},
                                 markers=True)
    st.plotly_chart(fig_aproveitamento)

    # Mostra a tabela
    st.subheader("Tabela de Desempenho")
    st.dataframe(duplas)
