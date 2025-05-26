def download_artifacts():
    print(f"🔍 Fetching artifact list from {repo} ...")
    page = 1
    per_page = 100
    total_downloaded = 0

    os.makedirs(artifact_dir, exist_ok=True)

    while True:
        print(f"🔄 Fetching page {page}...")
        url = f"https://api.github.com/repos/{repo}/actions/artifacts"
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to get artifacts page {page}: {response.status_code} {response.text}", file=sys.stderr)
            sys.exit(1)

        data = response.json()
        artifacts = data.get('artifacts', [])
        if not artifacts:
            if page == 1:
                print("ℹ️ No artifacts found.")
            break

        for artifact in artifacts:
            download_url = artifact['archive_download_url']
            name = artifact['name']
            print(f"⬇️ Downloading artifact: {name}")
            r = requests.get(download_url, headers=headers)
            if r.status_code != 200:
                print(f"❌ Failed to download {name}: {r.status_code}", file=sys.stderr)
                continue
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(artifact_dir)
            print(f"✅ Extracted to {artifact_dir}")
            total_downloaded += 1

        if len(artifacts) < per_page:
            break
        page += 1

    print(f"📥 Total artifacts downloaded and extracted: {total_downloaded}")
    return total_downloaded > 0

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
    
    # Download artifacts
    success = download_artifacts()
    if not success:
        print("⛔ No artifacts to process.")
        return

    # Load and merge data
    merged = load_and_merge(artifact_dir)
    if not merged:
        print("ℹ️ No new news items to send.")
        return

    # Build email and send it
    body = build_email_body(merged)
    subject = f"🌾 Agro Digest {datetime.now().strftime('%d/%m/%Y')}"
    send_email(body, subject)

    # After successful email sending, delete the artifacts folder
    #delete_artifacts_folder()

if __name__ == "__main__":
    main()
