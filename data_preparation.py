# data_preparation.py

import pandas as pd
from datetime import datetime, timedelta

def filtrar_por_periodo(df, periodo):
    """
    Filtra o DataFrame de acordo com o período selecionado.
    """
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
    """
    Prepara dados de vitórias, derrotas e aproveitamento para jogadores.
    """
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
    jogadores = jogadores.sort_values(by=["aproveitamento", "vitórias"], ascending=False)
    jogadores["aproveitamento"] = jogadores["aproveitamento"].round(0).astype(int).astype(str) + "%"
    jogadores["rank"] = range(1, jogadores.shape[0] + 1)
    return jogadores


def preparar_dados_duplas(df):
    """
    Prepara dados de vitórias, derrotas e aproveitamento para duplas.
    """
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
    duplas = duplas.sort_values(by=["aproveitamento", "vitórias"], ascending=False)
    duplas["aproveitamento"] = duplas["aproveitamento"].round(0).astype(int).astype(str) + "%"
    return duplas


def preparar_dados_confrontos_jogadores(df):
    """
    Prepara o saldo de vitórias entre os jogadores, retornando uma matriz
    em que a linha e a coluna representam os jogadores.
    """
    # Criar uma lista única de jogadores
    jogadores = list(
        df["winner1"].tolist()
        + df["winner2"].tolist()
        + df["loser1"].tolist()
        + df["loser2"].tolist()
    )
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
    saldo_final = saldo_final.set_index("Jogador")
    saldo_final = saldo_final.loc[
        ~saldo_final.index.astype(str).str.contains("Outro"),
        ~saldo_final.columns.astype(str).str.contains("Outro"),
    ]
    return saldo_final


def preparar_dados_controntos_duplas(df):
    """
    Prepara o saldo de confrontos entre duplas, retornando um DataFrame
    em que a linha e a coluna representam as duplas.
    """
    # Criar uma lista única de duplas
    duplas = sorted(set(df["dupla_winner"].tolist() + df["dupla_loser"].tolist()))

    # Criar um DataFrame de saldo de vitórias para duplas
    saldos_duplas = pd.DataFrame(0, index=duplas, columns=duplas)

    # Iterar pelas partidas para calcular o saldo de vitórias para duplas
    for _, row in df.iterrows():
        winner_dupla = row["dupla_winner"]
        loser_dupla = row["dupla_loser"]

        saldos_duplas.at[winner_dupla, loser_dupla] += 1
        saldos_duplas.at[loser_dupla, winner_dupla] -= 1

    # Resetar o índice para visualizar o saldo como um DataFrame plano
    saldo_final_duplas = saldos_duplas.reset_index()
    saldo_final_duplas.rename(columns={"index": "Dupla"}, inplace=True)
    saldo_final_duplas = saldo_final_duplas.set_index("Dupla")
    saldo_final_duplas = saldo_final_duplas.loc[
        ~saldo_final_duplas.index.astype(str).str.contains("Outro"),
        ~saldo_final_duplas.columns.astype(str).str.contains("Outro"),
    ]
    return saldo_final_duplas


def preparar_matriz_parcerias(df, style_dataframe):
    """
    Prepara uma matriz com o número de vezes que cada jogador jogou
    com outro jogador.
    """
    # Obter todos os jogadores únicos
    jogadores = list(
        df["winner1"].tolist()
        + df["winner2"].tolist()
        + df["loser1"].tolist()
        + df["loser2"].tolist()
    )
    jogadores = sorted(set(jogadores))

    # Criar matriz inicializada com zeros
    matriz_parcerias = pd.DataFrame(0, index=jogadores, columns=jogadores)

    # Preencher matriz com contagem de parcerias
    for _, row in df.iterrows():
        dupla1 = [row["winner1"], row["winner2"]]
        dupla2 = [row["loser1"], row["loser2"]]

        for dupla in [dupla1, dupla2]:
            for jogador1 in dupla:
                for jogador2 in dupla:
                    if jogador1 != jogador2:
                        matriz_parcerias.at[jogador1, jogador2] += 1

    matriz_parcerias = matriz_parcerias.loc[
        ~matriz_parcerias.index.astype(str).str.contains("Outro"),
        ~matriz_parcerias.columns.astype(str).str.contains("Outro"),
    ]

    # Aplicar estilo
    matriz_parcerias_styled = style_dataframe(matriz_parcerias)
    return matriz_parcerias_styled
