import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
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

def extrair_dados(page_data):
    """Extrai vencedores, perdedores e a data de submissão de uma página."""
    def extrair_multiselect(prop):
        return [item['name'] for item in prop.get('multi_select', [])] if prop and prop.get('type') == 'multi_select' else []

    winners = extrair_multiselect(page_data['properties'].get('Dupla 1'))
    losers = extrair_multiselect(page_data['properties'].get('Dupla 2'))
    submission_date = page_data['properties'].get('Submission time', {}).get('created_time')
    submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date() if submission_date else None

    return winners + losers + [submission_date]


def get_pages():
    """Consulta a API do Notion para obter todas as páginas do banco de dados."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 100}
    results = []

    while True:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    return results
    
# Funções auxiliares
def filtrar_por_periodo(df, periodo):
    """Filtra o DataFrame de acordo com o período selecionado."""

    if periodo == "Último dia":
        data_inicio = pd.to_datetime(df.index.max())
    elif periodo == "1 semana":
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
    jogadores = jogadores.loc[~jogadores["jogadores"].astype(str).str.contains("Outro"), :]

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
    duplas = duplas.loc[~duplas["duplas"].astype(str).str.contains("Outro"), :]
    
    return duplas

def preparar_dados_confrontos_jogadores(df):
    # Criar uma lista única de jogadores
    jogadores = list(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
    jogadores = sorted(set(jogadores))
    
    # Criar um DataFrame de saldo de vitórias
    saldos = pd.DataFrame(0, index=jogadores, columns=jogadores)
    
    # Iterar pelas partidas para calcular o saldo de vitórias
    for _, row in df.iterrows():
        winners = [row["winner1"], row["winner2"]]
        losers = [row["loser1"], row["loser2"]]
    
        for winner in winners:
            for loser in losers:
                saldos.at[winner, loser] += 1  # Vitória do jogador vencedor contra o perdedor
                saldos.at[loser, winner] -= 1  # Derrota do perdedor contra o vencedor
    
    # Resetar o índice para visualizar o saldo como um DataFrame plano
    saldo_final = saldos.reset_index()
    saldo_final.rename(columns={"index": "Jogador"}, inplace=True)
    saldo_final = saldo_final.set_index('Jogador')
    saldo_final = saldo_final.loc[~saldo_final.index.astype(str).str.contains("Outro"), 
                                  ~saldo_final.columns.astype(str).str.contains("Outro")]
    max_val = saldo_final.max().max()
    min_val = saldo_final.min().min()
    saldo_final = style_dataframe(saldo_final)
    return saldo_final


def preparar_dados_controntos_duplas(df):
    # Criar as combinações de duplas
    df["dupla_winner"] = df.apply(lambda row: " e ".join(sorted([row["winner1"], row["winner2"]])), axis=1)
    df["dupla_loser"] = df.apply(lambda row: " e ".join(sorted([row["loser1"], row["loser2"]])), axis=1)
    
    # Criar uma lista única de duplas
    duplas = sorted(set(df["dupla_winner"].tolist() + df["dupla_loser"].tolist()))
    
    # Criar um DataFrame de saldo de vitórias para duplas
    saldos_duplas = pd.DataFrame(0, index=duplas, columns=duplas)
    
    # Iterar pelas partidas para calcular o saldo de vitórias para duplas
    for _, row in df.iterrows():
        winner_dupla = row["dupla_winner"]
        loser_dupla = row["dupla_loser"]
    
        saldos_duplas.at[winner_dupla, loser_dupla] += 1  # Vitória da dupla vencedora contra a perdedora
        saldos_duplas.at[loser_dupla, winner_dupla] -= 1  # Derrota da dupla perdedora contra a vencedora
    
    # Resetar o índice para visualizar o saldo como um DataFrame plano
    saldo_final_duplas = saldos_duplas.reset_index()
    saldo_final_duplas.rename(columns={"index": "Dupla"}, inplace=True)
    saldo_final_duplas = saldo_final_duplas.set_index('Dupla')
    saldo_final_duplas = saldo_final_duplas.loc[~saldo_final_duplas.index.astype(str).str.contains("Outro"), 
                                                ~saldo_final_duplas.columns.astype(str).str.contains("Outro")]
    max_val = saldo_final_duplas.max().max()
    min_val = saldo_final_duplas.min().min()
    saldo_final_duplas = style_dataframe(saldo_final_duplas)
    return saldo_final_duplas


def exibir_graficos(df, eixo_x, titulo):
    """Exibe gráficos de vitórias, derrotas e aproveitamento."""
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(df, x=eixo_x, y="vitórias", title=f"Vitórias por {titulo}",
                          color_discrete_sequence=["steelblue"])
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(df, x=eixo_x, y="derrotas", title=f"Derrotas por {titulo}",
                          color_discrete_sequence=["indianred"])
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(df, x=eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}",
                                 markers=True)
    st.plotly_chart(fig_aproveitamento, use_container_width=True, config={"staticPlot": True})


def background_gradient(val, max_val, min_val):
    if val == 0:
        # Fundo preto para valores iguais a 0
        return "background-color: black; color: white;"
    elif val > 0:
        # Azul para valores positivos
        blue_intensity = min(255, int(255 * (val / max_val)))
        return f"background-color: rgba(0, 0, {blue_intensity}, 0.5);"
    elif val < 0:
        # Vermelho para valores negativos
        red_intensity = min(255, int(255 * (abs(val) / abs(min_val))))
        return f"background-color: rgba({red_intensity}, 0, 0, 0.5);"
    return "background-color: none;"


def style_dataframe(df):
    max_val = df.max().max()
    min_val = df.min().min()

    def style_cell(val):
        return background_gradient(val, max_val, min_val)

    return df.style.applymap(style_cell)

# Simulação de dados para exemplo
pages = get_pages()
data = [extrair_dados(page) for page in pages]
df = pd.DataFrame(data, columns=["winner1", "winner2", "loser1", "loser2", "date"]).set_index("date")

# Ordenar vencedores e perdedores
for i in range(df.shape[0]):
    df.iloc[i, 0:2] = df.iloc[i, 0:2].sort_values()
    df.iloc[i, 2:4] = df.iloc[i, 2:4].sort_values()

# Interface Streamlit
tab1, tab2, tab3, tab4 = st.tabs(["Jogadores", "Duplas", "Jogos", "Evolução"])

# Adicionar seleção de período em cada aba
periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]

with tab1:
    st.title("Análise de Desempenho dos Jogadores")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True, key="jogadores")
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    jogadores = preparar_dados_individuais(df_filtrado)
    exibir_graficos(jogadores, "jogadores", "Jogador")
    st.subheader("Estatíticas dos jogadores")
    st.dataframe(jogadores.set_index("jogadores").sort_values(by=['aproveitamento', 'vitórias'], ascending=False))
    st.subheader("Estatíticas dos confrontos")
    st.write("Esta tabela mostra o saldo de confrontos do jogador (na linha) em relação a cada adversário (na coluna).")
    st.dataframe(preparar_dados_confrontos_jogadores(df), use_container_width=True, key="duplas")

with tab2:
    st.title("Análise de Desempenho das Duplas")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True, key="jogos")
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    duplas = preparar_dados_duplas(df_filtrado)
    exibir_graficos(duplas, "duplas", "Dupla")
    st.subheader("Estatíticas das duplas")
    st.dataframe(duplas.set_index("duplas").sort_values(by=['aproveitamento', 'vitórias'], ascending=False))
    st.subheader("Estatíticas dos confrontos")
    st.write("Esta tabela mostra o saldo de confrontos da dupla (na linha) em relação a cada dupla adversária (na coluna).")
    st.dataframe(preparar_dados_controntos_duplas(df), use_container_width=True)

with tab3:
    st.title("Jogos Registrados")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)
    st.dataframe(df_filtrado.drop(['dupla_winner','dupla_loser'], axis=1).sort_index(ascending=False))

with tab4:
    st.title("Aproveitamento de Jogadores ao Longo do Tempo")

    # Lista única de jogadores
    jogadores = list(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
    jogadores = sorted(set(jogadores))

    # Criar subplots com uma linha para cada jogador
    fig = make_subplots(
        rows=len(jogadores),
        cols=1,
        shared_xaxes=True,  # Compartilhar eixo x
        vertical_spacing=0.02  # Espaçamento vertical entre os gráficos
    )

    # Iterar sobre cada jogador e calcular aproveitamento
    for idx, jogador in enumerate(jogadores, start=1):
        # Filtrar vitórias e derrotas por jogador
        vitorias = (df[["winner1", "winner2"]] == jogador).sum(axis=1)
        derrotas = (df[["loser1", "loser2"]] == jogador).sum(axis=1)

        # Consolidar por data
        vitorias_por_dia = vitorias.groupby(df.index).sum()
        derrotas_por_dia = derrotas.groupby(df.index).sum()

        # Calcular jogos totais e aproveitamento
        jogos_totais = vitorias_por_dia + derrotas_por_dia
        aproveitamento = (vitorias_por_dia / jogos_totais * 100).fillna(0)

        # Adicionar o gráfico do jogador aos subplots
        fig.add_scatter(
            x=aproveitamento.index,
            y=aproveitamento,
            mode="lines+markers",
            name=jogador,
            row=idx,
            col=1,
            line=dict(width=1),
            marker=dict(size=4)
        )

        # Adicionar o nome do jogador no eixo y
        fig.update_yaxes(title_text=jogador, row=idx, col=1)

    # Ajustar layout
    fig.update_layout(
        height=150 * len(jogadores),  # Altura total do gráfico
        showlegend=False,  # Não mostrar legenda
        title=None,
        margin=dict(l=40, r=20, t=20, b=20),
    )
    fig.update_xaxes(title_text=None)  # Nome para o eixo x compartilhado

    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
