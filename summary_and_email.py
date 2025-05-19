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

token = "GITHUB_TOKEN_O_PERSONAL_ACCESS_TOKEN"
repo = "usuario/repositorio"
headers = {"Authorization": f"token {token}"}

artifacts_url = f"https://api.github.com/repos/{repo}/actions/artifacts"
response = requests.get(artifacts_url, headers=headers)
data = response.json()

for artifact in data['artifacts']:
    download_url = artifact['archive_download_url']
    r = requests.get(download_url, headers=headers)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("artifacts_json")

def load_and_merge(input_dir):
    seen = set()
    merged = {}
    for path in glob.glob(f"{input_dir}/RSS_FEEDS_*.json"):
        data = json.load(open(path, encoding="utf-8"))
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
    body += f"<p>🗓️ Noticias de {days_desc} (mail generado: {datetime.now().strftime('%d/%m/%Y %H:%M')})</p>\n"
    for source, articles in merged.items():
        body += f"<h3>🔵 {source}</h3><ul>\n"
        # sort by published
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

    for var in ("SENDER_EMAIL","SENDER_PASSWORD","RECIPIENT_EMAIL"):
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

def main():
    ARTIFACT_DIR = sys.argv[1] if len(sys.argv)>1 else "."
    merged = load_and_merge(ARTIFACT_DIR)
    if not merged:
        print("ℹ️  No new items to send.")
        return
    body = build_email_body(merged)
    subject = f"🌾 Agro Digest {datetime.now().strftime('%d/%m/%Y')}"
    send_email(body, subject)

if __name__ == "__main__":
    main()
