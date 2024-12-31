import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests


# Configuração da API do Notion
NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_pages():
    """Consulta a API do Notion para obter todas as páginas do banco de dados."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 100}
    results = []

    while True:
        response = requests.post(url, json=payload, headers=HEADERS)
        data = response.json()
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    return results


def extrair_dados(page_data):
    """Extrai vencedores, perdedores e a data de submissão de uma página."""
    def extrair_multiselect(prop):
        return [item['name'] for item in prop.get('multi_select', [])] if prop else []

    winners = extrair_multiselect(page_data['properties'].get('Dupla 1'))
    losers = extrair_multiselect(page_data['properties'].get('Dupla 2'))
    submission_date = page_data['properties'].get('Submission time', {}).get('created_time')
    submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date() if submission_date else None

    return winners + losers + [submission_date]


def filtrar_por_periodo(df, periodo):
    """Filtra o DataFrame de acordo com o período selecionado."""
    periodos = {
        "Último dia": timedelta(days=1),
        "1 semana": timedelta(weeks=1),
        "1 mês": timedelta(weeks=4),
        "3 meses": timedelta(weeks=12),
        "6 meses": timedelta(weeks=26),
        "1 ano": timedelta(weeks=52),
        "Todos os dados": None
    }

    if periodo == "Todos os dados":
        return df
    data_inicio = datetime.now() - periodos[periodo]
    return df[df.index >= data_inicio.date()]


def calcular_estatisticas(df, nivel):
    """Calcula vitórias, derrotas e aproveitamento para jogadores ou duplas."""
    if nivel == "jogadores":
        col_w, col_l = ["winner1", "winner2"], ["loser1", "loser2"]
    elif nivel == "duplas":
        col_w, col_l = ["dupla_winner"], ["dupla_loser"]
    else:
        raise ValueError("Nível inválido. Use 'jogadores' ou 'duplas'.")

    vit_w = pd.Series([x for row in df[col_w].values for x in row]).value_counts()
    vit_l = pd.Series([x for row in df[col_l].values for x in row]).value_counts()

    entidades = sorted(set(vit_w.index).union(vit_l.index))
    vit_w = vit_w.reindex(entidades, fill_value=0)
    vit_l = vit_l.reindex(entidades, fill_value=0)

    aproveitamento = (vit_w / (vit_w + vit_l) * 100).fillna(0).round(0).astype(int)
    estatisticas = pd.DataFrame({
        nivel: entidades,
        "vitórias": vit_w.astype(int),
        "derrotas": vit_l.astype(int),
        "aproveitamento": aproveitamento.astype(str) + "%"
    }).sort_values(by=["aproveitamento", "vitórias"], ascending=False)

    return estatisticas


def preparar_matriz_saldos(df, col_w, col_l):
    """Prepara uma matriz de saldos entre vencedores e perdedores."""
    entidades = sorted(set(df[col_w].tolist() + df[col_l].tolist()))
    matriz = pd.DataFrame(0, index=entidades, columns=entidades)

    for _, row in df.iterrows():
        winners = row[col_w]
        losers = row[col_l]

        for w in winners:
            for l in losers:
                matriz.loc[w, l] += 1
                matriz.loc[l, w] -= 1

    return matriz


def exibir_graficos(df, eixo_x, titulo):
    """Exibe gráficos de vitórias, derrotas e aproveitamento."""
    st.subheader(f"Gráfico de Vitórias por {titulo}")
    fig = px.bar(df, x=eixo_x, y="vitórias", title=f"Vitórias por {titulo}", color_discrete_sequence=["steelblue"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Gráfico de Derrotas por {titulo}")
    fig = px.bar(df, x=eixo_x, y="derrotas", title=f"Derrotas por {titulo}", color_discrete_sequence=["indianred"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Gráfico de Aproveitamento por {titulo}")
    fig = px.line(df, x=eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}", markers=True, text="aproveitamento")
    st.plotly_chart(fig, use_container_width=True)


# Simulação de dados
pages = get_pages()
data = [extrair_dados(page) for page in pages]
df = pd.DataFrame(data, columns=["winner1", "winner2", "loser1", "loser2", "date"]).set_index("date")
df["dupla_winner"] = df.apply(lambda row: " e ".join(sorted([row["winner1"], row["winner2"]])), axis=1)
df["dupla_loser"] = df.apply(lambda row: " e ".join(sorted([row["loser1"], row["loser2"]])), axis=1)

# Interface Streamlit
tab1, tab2, tab3 = st.tabs(["Jogadores", "Duplas", "Confrontos"])
periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]

with tab1:
    st.title("Jogadores")
    periodo = st.radio("Selecione o período:", periodos, key="tab1")
    df_filtrado = filtrar_por_periodo(df, periodo)
    jogadores = calcular_estatisticas(df_filtrado, "jogadores")
    exibir_graficos(jogadores, "jogadores", "Jogador")

with tab2:
    st.title("Duplas")
    periodo = st.radio("Selecione o período:", periodos, key="tab2")
    df_filtrado = filtrar_por_periodo(df, periodo)
    duplas = calcular_estatisticas(df_filtrado, "duplas")
    exibir_graficos(duplas, "duplas", "Dupla")

with tab3:
    st.title("Confrontos")
    st.write("Confrontos registrados")
    matriz = preparar_matriz_saldos(df, "winner1", "loser1")
    st.dataframe(matriz)
