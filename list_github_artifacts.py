import os
import requests

OWNER = 'Vallistruqui-BP'
REPO = 'Automated-RSS-News-Reports'
API_URL = f'https://api.github.com/repos/{OWNER}/{REPO}/actions/artifacts'

def list_artifacts():
    GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set.")

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
    }

    artifacts = []
    page = 1
    per_page = 100

    while True:
        params = {'page': page, 'per_page': per_page}
        response = requests.get(API_URL, headers=headers, params=params)

        if response.status_code != 200:
            print(f'Error fetching artifacts: {response.status_code} {response.text}')
            return

        data = response.json()
        artifacts.extend(data.get('artifacts', []))

        # If fewer than per_page artifacts returned, we are on the last page
        if len(data.get('artifacts', [])) < per_page:
            break
        page += 1

    print(f"Total artifacts found: {len(artifacts)}\n")
    for art in artifacts:
        print(f"Name: {art['name']}")
        print(f"ID: {art['id']}")
        print(f"Size (bytes): {art['size_in_bytes']}")
        print(f"Expired: {art['expired']}")
        print(f"Expires at: {art['expires_at']}")
        print(f"URL: {art['url']}")
        print("-" * 40)

if __name__ == '__main__':
    list_artifacts()