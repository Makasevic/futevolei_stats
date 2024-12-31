# notion_api.py

import requests
from datetime import datetime
from config import DATABASE_ID, HEADERS

def extrair_dados(page_data):
    """
    Extrai vencedores, perdedores e a data de submissão de uma página.
    """
    def extrair_multiselect(prop):
        return [
            item["name"] for item in prop.get("multi_select", [])
        ] if prop and prop.get("type") == "multi_select" else []

    winners = extrair_multiselect(page_data["properties"].get("Dupla 1"))
    losers = extrair_multiselect(page_data["properties"].get("Dupla 2"))
    submission_date = page_data["properties"].get("Submission time", {}).get("created_time")
    submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date() if submission_date else None

    return winners + losers + [submission_date]


def get_pages():
    """
    Consulta a API do Notion para obter todas as páginas do banco de dados.
    """
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
