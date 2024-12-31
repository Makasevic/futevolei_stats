import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import requests

# =====================================================
# CONFIGURAÇÃO E CABEÇALHOS
# =====================================================
NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# =====================================================
# FUNÇÕES DE EXTRAÇÃO E PREPARAÇÃO DE DADOS
# =====================================================

def extrair_dados(page_data):
    """Extrai vencedores, perdedores e a data de submissão de uma página do Notion."""
    def extrair_multiselect(prop):
        return [item['name'] for item in prop.get('multi_select', [])] if prop and prop.get('type') == 'multi_select' else []
    
    winners = extrair_multiselect(page_data['properties'].get('Dupla 1'))
    losers = extrair_multiselect(page_data['properties'].get('Dupla 2'))
    submission_date = page_data['properties'].get('Submission time', {}).get('created_time')
    
    if submission_date:
        submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date()
    else:
        submission_date = None

    return winners + losers + [submission_date]


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


def preparar_dataframe(pages):
    """
    Recebe os dados brutos das páginas extraídas do Notion
    e retorna um DataFrame estruturado e indexado pela data.
    """
    data = [extrair_dados(page) for page in pages]
    df = pd.DataFrame(data, columns=["winner1", "winner2", "loser1", "loser2", "date"]).set_index("date")

    # Cria colunas de dupla vencedora e dupla perdedora
    df["dupla_winner"] = df.apply(lambda row: " e ".join(sorted([row["winner1"], row["winner2"]])), axis=1)
    df["dupla_loser"] = df.apply(lambda row: " e ".join(sorted([row["loser1"], row["loser2"]])), axis=1)

    # Ordenar vencedores e perdedores (garantindo consistência de nome)
    for i in range(df.shape[0]):
        df.iloc[i, 0:2] = df.iloc[i, 0:2].sort_values()
        df.iloc[i, 2:4] = df.iloc[i, 2:4].sort_values()
    
    return df


# =====================================================
# FUNÇÕES AUXILIARES (FILTROS E PREPARAÇÃO DE ESTATÍSTICAS)
# =====================================================

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

    # Remove "Outro" e ordena
    jogadores = jogadores.loc[~jogadores["jogadores"].astype(str).str.contains("Outro"), :]
    jogadores = jogadores.sort_values(by=['aproveitamento', 'vitórias'], ascending=False)

    # Ajuste de formatação
    jogadores["aproveitamento"] = jogadores["aproveitamento"].round(0).astype(int).astype(str) + "%"
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

    # Remove "Outro" e ordena
    duplas = duplas.loc[~duplas["duplas"].astype(str).str.contains("Outro"), :]
    duplas = duplas.sort_values(by=['aproveitamento', 'vitórias'], ascending=False)

    # Ajuste de formatação
    duplas["aproveitamento"] = duplas["aproveitamento"].round(0).astype(int).astype(str) + "%"

    return duplas


def preparar_dados_confrontos_jogadores(df):
    """Retorna DataFrame com saldo de confrontos entre jogadores (linha vs coluna)."""
    jogadores = sorted(set(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist()))
    saldos = pd.DataFrame(0, index=jogadores, columns=jogadores)

    for _, row in df.iterrows():
        winners = [row["winner1"], row["winner2"]]
        losers = [row["loser1"], row["loser2"]]
        for winner in winners:
            for loser in losers:
                saldos.at[winner, loser] += 1
                saldos.at[loser, winner] -= 1

    saldo_final = saldos.reset_index().rename(columns={"index": "Jogador"}).set_index("Jogador")
    saldo_final = saldo_final.loc[
        ~saldo_final.index.astype(str).str.contains("Outro"),
        ~saldo_final.columns.astype(str).str.contains("Outro")
    ]
    return saldo_final


def preparar_dados_confrontos_duplas(df):
    """Retorna DataFrame com saldo de confrontos entre duplas (linha vs coluna)."""
    duplas = sorted(set(df["dupla_winner"].tolist() + df["dupla_loser"].tolist()))
    saldos_duplas = pd.DataFrame(0, index=duplas, columns=duplas)

    for _, row in df.iterrows():
        winner_dupla = row["dupla_winner"]
        loser_dupla = row["dupla_loser"]
        saldos_duplas.at[winner_dupla, loser_dupla] += 1
        saldos_duplas.at[loser_dupla, winner_dupla] -= 1

    saldo_final_duplas = saldos_duplas.reset_index().rename(columns={"index": "Dupla"}).set_index("Dupla")
    saldo_final_duplas = saldo_final_duplas.loc[
        ~saldo_final_duplas.index.astype(str).str.contains("Outro"),
        ~saldo_final_duplas.columns.astype(str).str.contains("Outro")
    ]
    return saldo_final_duplas


def preparar_matriz_parcerias(df):
    """Prepara uma matriz com o número de vezes que cada jogador jogou COM outro jogador."""
    jogadores = sorted(set(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist()))
    matriz_parcerias = pd.DataFrame(0, index=jogadores, columns=jogadores)

    for _, row in df.iterrows():
        dupla1 = [row["winner1"], row["winner2"]]
        dupla2 = [row["loser1"], row["loser2"]]
        for dupla in [dupla1, dupla2]:
            for j1 in dupla:
                for j2 in dupla:
                    if j1 != j2:
                        matriz_parcerias.at[j1, j2] += 1

    matriz_parcerias = matriz_parcerias.loc[
        ~matriz_parcerias.index.astype(str).str.contains("Outro"),
        ~matriz_parcerias.columns.astype(str).str.contains("Outro")
    ]
    return style_dataframe(matriz_parcerias)


# =====================================================
# FUNÇÕES DE ESTILIZAÇÃO E GRÁFICOS
# =====================================================

def background_gradient(val, max_val, min_val):
    """Define o gradiente de cor de fundo, variando entre vermelho, azul e preto."""
    if val == 0:
        return "background-color: black; color: white;"
    elif val > 0:
        blue_intensity = min(255, int(255 * (val / max_val)))
        return f"background-color: rgba(0, 0, {blue_intensity}, 0.5);"
    else:  # val < 0
        red_intensity = min(255, int(255 * (abs(val) / abs(min_val))))
        return f"background-color: rgba({red_intensity}, 0, 0, 0.5);"


def style_dataframe(df):
    max_val = df.max().max()
    min_val = df.min().min()

    def style_cell(val):
        return background_gradient(val, max_val, min_val)

    return df.style.applymap(style_cell)


def exibir_graficos(df, eixo_x, titulo):
    """Exibe gráficos de vitórias, derrotas e aproveitamento."""
    st.subheader("Gráfico de Vitórias")
    fig_vitorias = px.bar(
        df, x=eixo_x, y="vitórias", title=f"Vitórias por {titulo}",
        color_discrete_sequence=["steelblue"]
    )
    fig_vitorias.update_xaxes(title="")
    st.plotly_chart(fig_vitorias, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Derrotas")
    fig_derrotas = px.bar(
        df, x=eixo_x, y="derrotas", title=f"Derrotas por {titulo}",
        color_discrete_sequence=["indianred"]
    )
    fig_derrotas.update_xaxes(title="")
    st.plotly_chart(fig_derrotas, use_container_width=True, config={"staticPlot": True})

    st.subheader("Gráfico de Aproveitamento")
    fig_aproveitamento = px.line(
        df, x=eixo_x, y="aproveitamento", title=f"Aproveitamento por {titulo}",
        markers=True, text="aproveitamento"
    )
    fig_aproveitamento.update_traces(textposition="top center", textfont_size=12)
    fig_aproveitamento.update_xaxes(title="")
    st.plotly_chart(fig_aproveitamento, use_container_width=True, config={"staticPlot": True})


# =====================================================
# FUNÇÕES DE LAYOUT DA APLICAÇÃO (STREAMLIT)
# =====================================================

def exibir_aba_jogadores(df):
    """Exibe a aba 1: Análise de Desempenho dos Jogadores."""
    st.title("Análise de Desempenho dos Jogadores")

    periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True, key="jogadores")

    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)

    # Estatísticas individuais
    jogadores = preparar_dados_individuais(df_filtrado)
    exibir_graficos(jogadores, "jogadores", "Jogador")

    st.subheader("Estatíticas dos jogadores")
    st.dataframe(jogadores.set_index("rank"))

    # Confrontos
    st.subheader("Estatíticas dos confrontos")
    st.write("Esta tabela mostra o saldo de confrontos do jogador (linha) em relação a cada adversário (coluna).")
    st.dataframe(style_dataframe(preparar_dados_confrontos_jogadores(df)), use_container_width=True, key="duplas")

    # Matriz de parcerias
    st.subheader("Matriz de Parcerias")
    st.write("Esta tabela mostra quantas vezes cada jogador (linha) jogou com outro jogador como dupla (coluna).")
    matriz_parcerias = preparar_matriz_parcerias(df)
    st.dataframe(matriz_parcerias, use_container_width=True)


def exibir_aba_detalhamento(df):
    """Exibe a aba 2: Análise Individual, podendo ser por Jogador ou por Dupla."""
    st.title("Análise Individual")

    # Botão de opção para alternar entre Jogador e Duplas
    analise_tipo = st.radio("Selecione o tipo de análise:", ["Jogador", "Duplas"], horizontal=True)

    if analise_tipo == "Jogador":
        st.subheader("Análise Individual do Jogador")

        # Lista de jogadores (removendo "Outro")
        jogadores_unicos = sorted(
            set(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
        )
        jogadores_unicos = [x for x in jogadores_unicos if "Outro" not in x]
        jogadores_unicos = ["Selecione um jogador"] + jogadores_unicos

        jogador_selecionado = st.selectbox("Selecione um jogador:", jogadores_unicos)

        if jogador_selecionado != "Selecione um jogador":
            # Cálculos de vitórias/derrotas para o jogador
            vitorias = (df[["winner1", "winner2"]] == jogador_selecionado).sum(axis=1)
            derrotas = (df[["loser1", "loser2"]] == jogador_selecionado).sum(axis=1)

            vitorias_por_dia = vitorias.groupby(df.index).sum()
            derrotas_por_dia = derrotas.groupby(df.index).sum()
            jogos_totais = vitorias_por_dia + derrotas_por_dia

            aproveitamento = (vitorias_por_dia / jogos_totais * 100).dropna().round(0)
            total_jogos = vitorias.sum() + derrotas.sum()
            total_vitorias = vitorias.sum()
            total_derrotas = derrotas.sum()
            media_aproveitamento = aproveitamento.mean()

            # Exibe estatísticas
            st.subheader("Informações gerais")
            st.write(f"**Jogador:** {jogador_selecionado}")
            st.write(f"**Número de jogos realizados:** {total_jogos}")
            st.write(f"**Vitórias:** {total_vitorias}")
            st.write(f"**Derrotas:** {total_derrotas}")
            st.write(f"**Aproveitamento médio:** {media_aproveitamento:.2f}%")

            # Gráfico de aproveitamento ao longo do tempo
            st.subheader("Aproveitamento ao longo do tempo")
            fig = px.line(
                x=aproveitamento.index,
                y=aproveitamento,
                title=f"Aproveitamento de {jogador_selecionado} ao longo do tempo",
                markers=True,
                text=aproveitamento.astype(str) + "%"
            )
            fig.update_traces(mode="lines+markers+text", textposition="top center", textfont_size=12)
            fig.update_xaxes(title="Data")
            fig.update_yaxes(title="Aproveitamento (%)")
            st.plotly_chart(fig, use_container_width=True)

            # Tabelas de maiores fregueses/carrascos
            st.subheader("Maiores Fregueses")
            df_saldo = preparar_dados_confrontos_jogadores(df)
            saldo_jogador = df_saldo.loc[jogador_selecionado, :]
            fregueses = saldo_jogador[saldo_jogador > 0].sort_values(ascending=False).head(5).reset_index()
            fregueses.columns = ["Jogador", "Saldo de Vitórias"]
            st.table(fregueses.set_index("Jogador"))

            st.subheader("Maiores Carrascos")
            carrascos = saldo_jogador[saldo_jogador < 0].sort_values().head(5).reset_index()
            carrascos.columns = ["Jogador", "Saldo de Vitórias"]
            st.table(carrascos.set_index("Jogador"))

        else:
            st.write("Por favor, selecione um jogador para visualizar os dados.")

    else:
        # Análise de Duplas
        st.subheader("Análise Individual da Dupla")

        duplas = preparar_dados_duplas(df)
        dupla_selecionada = st.selectbox(
            "Selecione uma dupla:",
            ["Selecione uma dupla"] + sorted(duplas["duplas"].tolist())
        )

        if dupla_selecionada != "Selecione uma dupla":
            dupla_vitorias = (df["dupla_winner"] == dupla_selecionada).astype(int)
            dupla_derrotas = (df["dupla_loser"] == dupla_selecionada).astype(int)

            # Consolidar por data
            vitorias_por_dia = dupla_vitorias.groupby(df.index).sum()
            derrotas_por_dia = dupla_derrotas.groupby(df.index).sum()

            # Calcular jogos totais e aproveitamento
            jogos_totais = vitorias_por_dia + derrotas_por_dia
            aproveitamento_por_dia = (vitorias_por_dia / jogos_totais * 100).dropna().round(2)

            total_jogos = vitorias_por_dia.sum() + derrotas_por_dia.sum()
            total_vitorias = vitorias_por_dia.sum()
            total_derrotas = derrotas_por_dia.sum()
            media_aproveitamento = aproveitamento_por_dia.mean()

            st.subheader("Informações gerais")
            st.write(f"**Dupla:** {dupla_selecionada}")
            st.write(f"**Número de jogos realizados:** {total_jogos}")
            st.write(f"**Vitórias:** {total_vitorias}")
            st.write(f"**Derrotas:** {total_derrotas}")
            st.write(f"**Aproveitamento médio:** {media_aproveitamento:.2f}%")

            # Gráfico de aproveitamento ao longo do tempo
            st.subheader("Aproveitamento ao longo do tempo")
            fig = px.line(
                x=aproveitamento_por_dia.index,
                y=aproveitamento_por_dia,
                title=f"Aproveitamento de {dupla_selecionada} ao longo do tempo",
                markers=True,
                text=aproveitamento_por_dia.astype(str) + "%"
            )
            fig.update_traces(mode="lines+markers+text", textposition="top center", textfont_size=12)
            fig.update_xaxes(title="Data", type="category")
            fig.update_yaxes(title="Aproveitamento (%)")
            st.plotly_chart(fig, use_container_width=True)

            # Saldo de confrontos entre duplas
            df_saldo_duplas = preparar_dados_confrontos_duplas(df)
            saldo_dupla = df_saldo_duplas.loc[dupla_selecionada, :]

            # Maiores fregueses (saldo positivo)
            fregueses = saldo_dupla[saldo_dupla > 0].sort_values(ascending=False).head(5).reset_index()
            fregueses.columns = ["Dupla", "Saldo de Vitórias"]

            # Maiores carrascos (saldo negativo)
            carrascos = saldo_dupla[saldo_dupla < 0].sort_values().head(5).reset_index()
            carrascos.columns = ["Dupla", "Saldo de Vitórias"]

            st.subheader("Maiores Fregueses")
            st.table(fregueses.set_index("Dupla"))

            st.subheader("Maiores Carrascos")
            st.table(carrascos.set_index("Dupla"))
        else:
            st.write("Por favor, selecione uma dupla para visualizar os dados.")


def exibir_aba_jogos(df):
    """Exibe a aba 3: Lista dos jogos registrados."""
    st.title("Jogos Registrados")

    periodos = ["Último dia", "1 semana", "1 mês", "3 meses", "6 meses", "1 ano", "Todos os dados"]
    periodo_selecionado = st.radio("Selecione o período:", periodos, horizontal=True)

    df_filtrado = filtrar_por_periodo(df, periodo_selecionado)
    st.dataframe(df_filtrado.drop(['dupla_winner','dupla_loser'], axis=1).sort_index(ascending=False))


# =====================================================
# MAIN (EXECUÇÃO DO STREAMLIT)
# =====================================================

def main():
    # 1) Buscar dados do Notion
    pages = get_pages()

    # 2) Preparar o DataFrame
    df = preparar_dataframe(pages)

    # 3) Criar as abas
    tab1, tab2, tab3 = st.tabs(["Jogadores", "Detalhamento", "Jogos"])

    with tab1:
        exibir_aba_jogadores(df)

    with tab2:
        exibir_aba_detalhamento(df)

    with tab3:
        exibir_aba_jogos(df)


# Ponto de entrada do Streamlit
if __name__ == "__main__":
    main()
