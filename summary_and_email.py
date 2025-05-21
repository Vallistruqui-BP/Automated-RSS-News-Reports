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

# Cargar token desde variable de entorno
token = os.getenv("MY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") or os.getenv("PAT_TOKEN")
if not token:
    print("❌ Missing GitHub token. Set GITHUB_TOKEN or PAT_TOKEN environment variable.", file=sys.stderr)
    sys.exit(1)

repo = "Vallistruqui-BP/Automated-RSS-News-Reports"
headers = {"Authorization": f"token {token}"}

# Directorio destino (por defecto)
artifact_dir = sys.argv[1] if len(sys.argv) > 1 else "artifacts_json"

def download_artifacts():
    print(f"🔍 Fetching artifact list from {repo} ...")
    response = requests.get(f"https://api.github.com/repos/{repo}/actions/artifacts", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get artifacts: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)
    data = response.json()

    if not data.get('artifacts'):
        print("ℹ️ No artifacts found.")
        return False

    os.makedirs(artifact_dir, exist_ok=True)

    for artifact in data['artifacts']:
        download_url = artifact['archive_download_url']
        print(f"⬇️ Downloading artifact: {artifact['name']}")
        r = requests.get(download_url, headers=headers)
        if r.status_code != 200:
            print(f"❌ Failed to download {artifact['name']}: {r.status_code}", file=sys.stderr)
            continue
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(artifact_dir)
        print(f"✅ Extracted to {artifact_dir}")

    return True

def load_and_merge(input_dir):
    seen = set()
    merged = {}
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
    return merged

def build_email_body(merged, days_desc="last period"):
    body = "<h2>🌾 Resumen Agro Consolidado 🌾</h2>\n"
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

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER, PASS)
        s.send_message(msg)
    print("✅ Summary email sent!")

""" def delete_artifacts_folder():
    if os.path.exists(artifact_dir):
        shutil.rmtree(artifact_dir)
        print(f"🧹 Deleted folder {artifact_dir}")
 """
def main():
    print("🚀 Starting process...")
    success = download_artifacts()
    if not success:
        print("⛔ No artifacts to process.")
        return

    merged = load_and_merge(artifact_dir)
    if not merged:
        print("ℹ️ No new news items to send.")
#        delete_artifacts_folder()
        return

    body = build_email_body(merged)
    subject = f"🌾 Agro Digest {datetime.now().strftime('%d/%m/%Y')}"
    send_email(body, subject)
#    delete_artifacts_folder()

if __name__ == "__main__":
    main()