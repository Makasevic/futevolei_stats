import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import requests
import random


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
    jogadores = jogadores.sort_values(by=['aproveitamento', 'vitórias'], ascending=False)
    jogadores["aproveitamento"] = jogadores["aproveitamento"].round(0).astype(int) .astype(str) + "%"
    jogadores["rank"] = range(1, jogadores.shape[0] + 1)
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
    duplas = duplas.sort_values(by=['aproveitamento', 'vitórias'], ascending=False)
    duplas["aproveitamento"] = duplas["aproveitamento"].round(0).astype(int) .astype(str) + "%"
    
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
    saldo_final_duplas = style_dataframe(saldo_final_duplas)
    return saldo_final_duplas


def preparar_matriz_parcerias(df):
    """Prepara uma matriz com o número de vezes que cada jogador jogou com outro jogador."""
    # Obter todos os jogadores únicos
    jogadores = list(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
    jogadores = sorted(set(jogadores))

    # Criar matriz inicializada com zeros
    matriz_parcerias = pd.DataFrame(0, index=jogadores, columns=jogadores)

    # Preencher matriz com contagem de parcerias
    for _, row in df.iterrows():
        # Vencedores e perdedores
        dupla1 = [row["winner1"], row["winner2"]]
        dupla2 = [row["loser1"], row["loser2"]]
        
        # Contar parcerias
        for dupla in [dupla1, dupla2]:
            for jogador1 in dupla:
                for jogador2 in dupla:
                    if jogador1 != jogador2:  # Não contar parcerias consigo mesmo
                        matriz_parcerias.at[jogador1, jogador2] += 1

    matriz_parcerias = matriz_parcerias.loc[~matriz_parcerias.index.astype(str).str.contains("Outro"), 
                              ~matriz_parcerias.columns.astype(str).str.contains("Outro")]
        
    matriz_parcerias = style_dataframe(matriz_parcerias)
    return matriz_parcerias


def exibir_graficos(df, eixo_x, titulo):
    """Exibe gráficos de vitórias, derrotas e aproveitamento."""
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(df, x=eixo_x, y="vitórias", title=f"Vitórias por {titulo}",
                          color_discrete_sequence=["steelblue"])
    fig_vitorias.update_xaxes(title="")  # Remove a label do eixo x
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(df, x=eixo_x, y="derrotas", title=f"Derrotas por {titulo}",
                          color_discrete_sequence=["indianred"])
    fig_derrotas.update_xaxes(title="")  # Remove a label do eixo x
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(df, x=eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}", markers=True, text="aproveitamento")
    fig_aproveitamento.update_traces(textposition="top center", textfont_size=12)
    fig_aproveitamento.update_xaxes(title="")  # Remove a label do eixo x
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
tab1, tab2, tab3, tab4 = st.tabs(["Jogadores", "Duplas", "Jogos", "Detalhamento"])

# Adicionar seleção de período em cada aba
periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]


with tab1:
    st.title("Análise de Desempenho dos Jogadores")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True, key="jogadores")
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    jogadores = preparar_dados_individuais(df_filtrado)
    exibir_graficos(jogadores, "jogadores", "Jogador")
    st.subheader("Estatíticas dos jogadores")
    st.dataframe(jogadores.set_index("rank"))
    st.subheader("Estatíticas dos confrontos")
    st.write("Esta tabela mostra o saldo de confrontos do jogador (linha) em relação a cada adversário (coluna).")
    st.dataframe(style_dataframe(preparar_dados_confrontos_jogadores(df)), use_container_width=True, key="duplas")
    st.subheader("Matriz de Parcerias")
    st.write("Esta tabela mostra quantas vezes cada jogador (linha) jogou com outro jogador como dupla (coluna).")
    matriz_parcerias = preparar_matriz_parcerias(df)
    st.dataframe(matriz_parcerias, use_container_width=True)

with tab2:
    st.title("Análise de Desempenho das Duplas")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True, key="jogos")
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    duplas = preparar_dados_duplas(df_filtrado)
    exibir_graficos(duplas, "duplas", "Dupla")
    st.subheader("Estatíticas das duplas")
    st.dataframe(duplas.set_index("duplas"))
    st.subheader("Estatíticas dos confrontos")
    st.write("Esta tabela mostra o saldo de confrontos da dupla (na linha) em relação a cada dupla adversária (na coluna).")
    st.dataframe(preparar_dados_controntos_duplas(df), use_container_width=True)

with tab3:
    st.title("Jogos Registrados")
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)
    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)
    st.dataframe(df_filtrado.drop(['dupla_winner','dupla_loser'], axis=1).sort_index(ascending=False))


with tab4:
    st.title("Análise Individual do Jogador")

    # Lista de jogadores
    jogadores = list(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
    jogadores = sorted(set(jogadores))
    jogadores = [x for x in jogadores if "Outro" not in x]
    # Escolher aleatoriamente um jogador como padrão
    jogador_default = random.choice(jogadores)
    # Dropdown para selecionar o jogador
    jogador_selecionado = st.selectbox("Selecione um jogador:", jogadores, index=jogadores.index(jogador_default))
    # Remover o jogador selecionado da lista
    jogadores = [x for x in jogadores if x != jogador_selecionado]
    

    # Filtro de vitórias e derrotas por jogador
    vitorias = (df[["winner1", "winner2"]] == jogador_selecionado).sum(axis=1)
    derrotas = (df[["loser1", "loser2"]] == jogador_selecionado).sum(axis=1)
    
    # Consolidar por data
    vitorias_por_dia = vitorias.groupby(df.index).sum()
    derrotas_por_dia = derrotas.groupby(df.index).sum()
    
    # Calcular jogos totais e aproveitamento
    jogos_totais = vitorias_por_dia + derrotas_por_dia
    aproveitamento = (vitorias_por_dia / jogos_totais * 100).dropna().round(0)
    
    # Informações gerais do jogador
    total_jogos = vitorias.sum() + derrotas.sum()
    total_vitorias = vitorias.sum()
    total_derrotas = derrotas.sum()
    media_aproveitamento = aproveitamento.mean()

    st.subheader("Informações gerais")
    st.write(f"**Jogador:** {jogador_selecionado}")
    st.write(f"**Número de jogos realizados:** {total_jogos}")
    st.write(f"**Vitórias:** {total_vitorias}")
    st.write(f"**Derrotas:** {total_derrotas}")
    st.write(f"**Aproveitamento médio:** {media_aproveitamento:.2f}%")

    # Gráfico de aproveitamento do jogador
    st.subheader("Aproveitamento ao longo do tempo")
    fig = px.line(
        x=aproveitamento.index, 
        y=aproveitamento, 
        title=f"Aproveitamento de {jogador_selecionado} ao longo do tempo",
        markers=True,
        text=aproveitamento.astype(str) + "%"  # Adiciona as labels nos pontos
    )
    fig.update_traces(mode="lines+markers+text", textposition="top center", textfont_size=12)
    
    # Formatar o eixo X para exibir apenas as datas
    fig.update_xaxes(
        type="category", 
        tickformat="%b %d, %Y",  # Formato para mostrar mês, dia e ano (sem horas)
        title="Data"
    )
    fig.update_yaxes(title="Aproveitamento (%)")
    st.plotly_chart(fig, use_container_width=True)

    # fregueses e carrascos
    df_saldo = preparar_dados_confrontos_jogadores(df)
    saldo_jogador = df_saldo.loc[jogador_selecionado, :]
    
    # Separar os maiores fregueses (saldo positivo) e maiores carrascos (saldo negativo)
    fregueses = saldo_jogador[saldo_jogador > 0].sort_values(ascending=False).head(5).reset_index()
    fregueses.columns = ["Jogador", "Saldo de Vitórias"]
    
    carrascos = saldo_jogador[saldo_jogador < 0].sort_values().head(5).reset_index()
    carrascos.columns = ["Jogador", "Saldo de Vitórias"]
    
    # Exibir as tabelas
    st.subheader("Maiores Fregueses")
    st.table(fregueses.set_index("Jogador"))
    
    st.subheader("Maiores Carrascos")
    st.table(carrascos.set_index("Jogador"))


    # Calcular parcerias
    parcerias = []
    for _, row in df.iterrows():
        dupla1 = [row["winner1"], row["winner2"]]
        dupla2 = [row["loser1"], row["loser2"]]
        
        if jogador_selecionado in dupla1:
            parceiro = dupla1[0] if dupla1[1] == jogador_selecionado else dupla1[1]
            parcerias.append(parceiro)
        elif jogador_selecionado in dupla2:
            parceiro = dupla2[0] if dupla2[1] == jogador_selecionado else dupla2[1]
            parcerias.append(parceiro)
    
    # Contagem de parcerias
    contagem_parcerias = pd.Series(parcerias).value_counts()
    contagem_parcerias = contagem_parcerias.reindex(index=jogadores)
    contagem_parcerias = contagem_parcerias.fillna(0).sort_values(ascending=False).astype(int)
    
    # Top 5 parcerias mais frequentes
    st.subheader("Top 5 parcerias mais frequentes")
    top5_mais = contagem_parcerias.head(5).reset_index()
    top5_mais.columns = ["Jogador", "Jogos"]
    st.table(top5_mais.set_index("Jogador"))
    
    # Top 5 parcerias menos frequentes
    st.subheader("Top 5 parcerias menos frequentes")
    top5_menos = contagem_parcerias.tail(5).reset_index()
    top5_menos.columns = ["Jogador", "Jogos"]
    st.table(top5_menos.set_index("Jogador"))

    

