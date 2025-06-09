#!/usr/bin/env python3
import glob
import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
import requests
import zipfile
import io
import shutil

OWNER = 'Vallistruqui-BP'
REPO = 'Automated-RSS-News-Reports'
API_URL = f'https://api.github.com/repos/{OWNER}/{REPO}/actions/artifacts'

# Load token from environment variable
token = os.getenv("MY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") or os.getenv("PAT_TOKEN")
if not token:
    print("❌ Missing GitHub token. Set GITHUB_TOKEN or PAT_TOKEN environment variable.", file=sys.stderr)
    sys.exit(1)

# Common headers
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

artifact_dir = "artifacts_json"  # Default artifact directory

def fetch_and_process_artifacts():
    total_count = 0
    page = 1
    per_page = 1000

    os.makedirs(artifact_dir, exist_ok=True)

    while True:
        params = {'page': page, 'per_page': per_page}
        response = requests.get(API_URL, headers=headers, params=params)

        if response.status_code != 200:
            print(f'❌ Error fetching artifacts: {response.status_code} {response.text}')
            return

        data = response.json()
        artifacts = data.get('artifacts', [])
        total_count += len(artifacts)

        # Process each artifact (download and delete)
        for artifact in artifacts:
            artifact_id = artifact['id']
            artifact_name = artifact['name']
            download_url = artifact['archive_download_url']

            # Download artifact
            print(f"⬇️ Downloading artifact: {artifact_name}")
            download_response = requests.get(download_url, headers=headers)
            if download_response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(download_response.content)) as z:
                    z.extractall(artifact_dir)
                print(f"✅ Extracted to {artifact_dir}")
            else:
                print(f"❌ Failed to download {artifact_name}: {download_response.status_code}")

            # Delete artifact
            delete_url = f"{API_URL}/{artifact_id}"
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code == 204:
                print(f"✅ Successfully deleted artifact: {artifact_name}")
            else:
                print(f"❌ Failed to delete artifact: {artifact_name} - {delete_response.status_code} {delete_response.text}")

        if len(artifacts) < per_page:
            break
        page += 1

    print(f"Total artifacts processed and deleted: {total_count}")

def load_and_merge(input_dir):
    seen = set()
    merged = {}
    print(f"🔍 Loading and merging files from {input_dir}...")
    for path in glob.glob(f"{input_dir}/RSS_FEEDS_*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load {path}: {e}", file=sys.stderr)
            continue
        for source, articles in data.items():
            merged.setdefault(source, [])
            for art in articles:
                key = art["link"]
                if key not in seen:
                    seen.add(key)
                    merged[source].append(art)
    print(f"🔄 Merged {len(merged)} sources.")
    return merged

def build_email_body(merged, days_desc="last period"):
    body = "<h2> Resumen Diario Noticias</h2>\n"
    body += f"<p>🗓️ Noticias de {days_desc} (generado: {datetime.now().strftime('%d/%m/%Y %H:%M')})</p>\n"
    for source, articles in merged.items():
        body += f"<h3>🔵 {source}</h3><ul>\n"
        articles.sort(key=lambda x: x["published"])
        for art in articles:
            dt = datetime.fromisoformat(art["published"]).strftime("%d/%m %H:%M")
            body += f"<li>📰 [{dt}] <a href='{art['link']}' target='_blank'>{art['title']}</a></li>\n"
        body += "</ul>\n"
    body += "<hr><p style='font-size:small;color:gray;'>Email generado automáticamente</p>"
    return body

def send_email(html_body, subject):
    SENDER = os.getenv("SENDER_EMAIL")
    PASS   = os.getenv("SENDER_PASSWORD")
    TO     = os.getenv("RECIPIENT_EMAIL")

    for var in ("SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"):
        if not os.getenv(var):
            print(f"❌ Missing {var}", file=sys.stderr)
            sys.exit(1)

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SENDER, PASS)
            s.send_message(msg)
        print("✅ Summary email sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    print("🚀 Starting process...")

    # Download and delete artifacts
    fetch_and_process_artifacts()

    # Load and merge data
    merged = load_and_merge(artifact_dir)
    if not merged:
        print("ℹ️ No new news items to send.")
        return

    # Build email and send it
    body = build_email_body(merged)
    subject = f"🌾 Agro Digest {datetime.now().strftime('%d/%m/%Y')}"
    send_email(body, subject)

if __name__ == "__main__":
    main()
