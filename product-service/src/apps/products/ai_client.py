import os
import requests


def rag_recommend(query):
    ai_service_url = os.environ.get('AI_SERVICE_URL', 'http://ai-service:8000')
    try:
        resp = requests.get(f'{ai_service_url}/recommend', params={'q': query}, timeout=2)
        if resp.status_code == 200:
            return resp.json().get('recommendations', [])
    except Exception:
        pass
    return []
