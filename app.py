import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests


# Funções auxiliares
def extrair_dados(page_data):
    """Extrai vencedores, perdedores e a data de submissão da página."""
    def extrair_multiselect(prop):
        return [item['name'] for item in prop.get('multi_select', [])] if prop and prop.get('type') == 'multi_select' else []

    winners = extrair_multiselect(page_data['properties'].get('Dupla 1'))
    losers = extrair_multiselect(page_data['properties'].get('Dupla 2'))
    
    submission_date = page_data['properties'].get('Submission time', {}).get('created_time')
    submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date() if submission_date else None
    
    return winners + losers + [submission_date]


def get_pages(num_pages=None):
    """Consulta a API do Notion para obter páginas do banco de dados."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 100 if num_pages is None else num_pages}
    results = []
    
    while True:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    
    return results


def preparar_dados_jogadores(df):
    """Processa o DataFrame de partidas e gera estatísticas de jogadores."""
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
    return jogadores[~jogadores["jogadores"].str.contains("Outro")]


def preparar_dados_duplas(df):
    """Processa o DataFrame de partidas e gera estatísticas de duplas."""
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
    return duplas[~duplas["duplas"].str.contains("Outro")]


def exibir_graficos(df, titulo_eixo_x, titulo):
    """Gera gráficos de vitórias, derrotas e aproveitamento para um DataFrame."""
    st.subheader(f"Gráfico de Vitórias")
    fig_vitorias = px.bar(df, x=titulo_eixo_x, y="vitórias", title=f"Vitórias por {titulo}",
                          labels={"vitórias": "Vitórias", titulo_eixo_x: titulo},
                          color_discrete_sequence=["red"])
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader(f"Gráfico de Derrotas")
    fig_derrotas = px.bar(df, x=titulo_eixo_x, y="derrotas", title=f"Derrotas por {titulo}",
                          labels={"derrotas": "Derrotas", titulo_eixo_x: titulo},
                          color_discrete_sequence=["blue"])
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader(f"Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(df, x=titulo_eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}",
                                 labels={"aproveitamento": "Aproveitamento (%)", titulo_eixo_x: titulo},
                                 markers=True)
    st.plotly_chart(fig_aproveitamento, use_container_width=True, config={"staticPlot": True})


# Configuração da API do Notion
NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Obtenção e processamento de dados
pages = get_pages()
data = [extrair_dados(page) for page in pages]
df = pd.DataFrame(data, columns=["winner1", "winner2", "loser1", "loser2", "date"]).set_index("date")

# Ordenar vencedores e perdedores
df.iloc[:, :2] = df.iloc[:, :2].apply(sorted, axis=1)
df.iloc[:, 2:4] = df.iloc[:, 2:4].apply(sorted, axis=1)

# Preparar dados para exibição
jogadores = preparar_dados_jogadores(df)
duplas = preparar_dados_duplas(df)

# Interface do Streamlit
tab1, tab2 = st.tabs(["Jogadores", "Duplas"])

with tab1:
    st.title("Análise de Desempenho dos Jogadores")
    exibir_graficos(jogadores, "jogadores", "Jogador")
    st.subheader("Tabela de Desempenho")
    st.dataframe(jogadores.set_index("jogadores"))

with tab2:
    st.title("Análise de Desempenho das Duplas")
    exibir_graficos(duplas, "duplas", "Dupla")
    st.subheader("Tabela de Desempenho")
    st.dataframe(duplas.set_index("duplas"))
