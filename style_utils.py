# style_utils.py

def background_gradient(val, max_val, min_val):
    if val == 0:
        # Fundo preto para valores iguais a 0
        return "background-color: black; color: white;"
    elif val > 0:
        # Azul para valores positivos
        blue_intensity = min(255, int(255 * (val / max_val))) if max_val != 0 else 0
        return f"background-color: rgba(0, 0, {blue_intensity}, 0.5);"
    elif val < 0:
        # Vermelho para valores negativos
        red_intensity = min(255, int(255 * (abs(val) / abs(min_val)))) if min_val != 0 else 0
        return f"background-color: rgba({red_intensity}, 0, 0, 0.5);"
    return "background-color: none;"


def style_dataframe(df):
    max_val = df.max().max()
    min_val = df.min().min()

    def style_cell(val):
        return background_gradient(val, max_val, min_val)

    return df.style.applymap(style_cell)
