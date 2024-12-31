import pandas as pd
from datetime import datetime, timedelta

def filtrar_por_periodo(df, periodo):
    """Filtra o DataFrame de acordo com o período selecionado."""
    periodos = {
        "Último dia": timedelta(days=1),
        "1 semana": timedelta(weeks=1),
        "1 mês": timedelta(weeks=4),
        "3 meses": timedelta(weeks=12),
        "6 meses": timedelta(weeks=26),
        "1 ano": timedelta(weeks=52),
    }

    if periodo in periodos:
        data_inicio = datetime.now() - periodos[periodo]
        return df[df.index >= data_inicio.date()]
    return df

def calcular_estatisticas(df, nivel):
    """Calcula estatísticas de vitórias, derrotas e aproveitamento para jogadores ou duplas."""
    if nivel == "jogadores":
        col_w, col_l = ["winner1", "winner2"], ["loser1", "loser2"]
        estatisticas_w = pd.Series([x for row in df[col_w].values for x in row]).value_counts()
        estatisticas_l = pd.Series([x for row in df[col_l].values for x in row]).value_counts()
    elif nivel == "duplas":
        col_w, col_l = ["dupla_winner"], ["dupla_loser"]
        estatisticas_w = df[col_w[0]].value_counts()
        estatisticas_l = df[col_l[0]].value_counts()
    else:
        raise ValueError("Nível inválido. Use 'jogadores' ou 'duplas'.")

    entidades = sorted(set(estatisticas_w.index).union(estatisticas_l.index))
    estatisticas_w = estatisticas_w.reindex(entidades, fill_value=0)
    estatisticas_l = estatisticas_l.reindex(entidades, fill_value=0)

    aproveitamento = (estatisticas_w / (estatisticas_w + estatisticas_l) * 100).round(0)
    return pd.DataFrame({
        nivel: entidades,
        "vitórias": estatisticas_w.astype(int),
        "derrotas": estatisticas_l.astype(int),
        "aproveitamento": aproveitamento.fillna(0).astype(int).astype(str) + "%"
    }).sort_values(by=["aproveitamento", "vitórias"], ascending=False)



def preparar_matriz_saldos(df, nivel):
    """Prepara uma matriz de saldo de confrontos para jogadores ou duplas."""
    col_w, col_l = (["winner1", "winner2"], ["loser1", "loser2"]) if nivel == "jogadores" else (["dupla_winner"], ["dupla_loser"])
    entidades = sorted(set(df[col_w[0]].tolist() + df[col_l[0]].tolist()))
    matriz = pd.DataFrame(0, index=entidades, columns=entidades)

    for _, row in df.iterrows():
        winners = row[col_w]
        losers = row[col_l]
        for w in winners:
            for l in losers:
                matriz.loc[w, l] += 1
                matriz.loc[l, w] -= 1

    return matriz

def preparar_matriz_parcerias(df):
    """Prepara uma matriz com o número de vezes que cada jogador jogou com outro jogador."""
    jogadores = list(df["winner1"].tolist() + df["winner2"].tolist() + df["loser1"].tolist() + df["loser2"].tolist())
    matriz = pd.DataFrame(0, index=sorted(set(jogadores)), columns=sorted(set(jogadores)))

    for _, row in df.iterrows():
        for dupla in [row[["winner1", "winner2"]].values, row[["loser1", "loser2"]].values]:
            for jogador1 in dupla:
                for jogador2 in dupla:
                    if jogador1 != jogador2:
                        matriz.loc[jogador1, jogador2] += 1

    return matriz
