import os
import requests
from datetime import datetime

NOTION_TOKEN = "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"
DATABASE_ID = "165d12cbe28e80eb9f7ad9d83cdd7115"

if not NOTION_TOKEN or not DATABASE_ID:
    raise ValueError("Token ou ID do banco de dados do Notion não configurado")

headers = {
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
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data["results"])
            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erro ao acessar a API do Notion: {e}")

    return results

def extrair_dados(page_data):
    """Extrai vencedores, perdedores e a data de submissão de uma página."""
    def extrair_multiselect(prop):
        return [item['name'] for item in prop.get('multi_select', [])] if prop and prop.get('type') == 'multi_select' else []

    winners = extrair_multiselect(page_data['properties'].get('Dupla 1'))
    losers = extrair_multiselect(page_data['properties'].get('Dupla 2'))
    submission_date = page_data['properties'].get('Submission time', {}).get('created_time')
    submission_date = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%S.%fZ").date() if submission_date else None

    return winners + losers + [submission_date]
