import feedparser
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time
import unicodedata
import sys

# Email settings from GitHub Secrets
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Safety check for missing env vars
missing = []
if not SENDER_EMAIL: missing.append("SENDER_EMAIL")
if not SENDER_PASSWORD: missing.append("SENDER_PASSWORD")
if not RECIPIENT_EMAIL: missing.append("RECIPIENT_EMAIL")

if missing:
    print(f"❌ ERROR: Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

KEYWORDS = [
    "maiz",
    "sorgo",
    "girasol",
    "trigo",
    "importaciones",
    "importacion",
    "bioceres",
    "remingtom",
    "agidea",
    "corteva",
    "syngenta",
    "gdm",
    "los grobo",
    "limagrain",
    "rizobacter",
    "bayer"
]

# 📰 List of RSS Feeds from top Argentinian news outlets
# CLARIN: http://clarin.com/rss.html
# LA NACION: https://www.lanacion.com.ar/arc/outboundfeeds/rss/
# AGROFY: Nose
# INFOCAMPO: https://www.infocampo.com.ar/feed/
# BICHOS DE CAMPO: https://www.infocampo.com.ar/feed/
# AGROSITIO: Nose
# CAMPOENACCION: Nose
# AGROLINK: Nose
# REVISTACHACRA: Nose
# VALORSOJA:https://www.valorsoja.com/feed/
# AGROGLOBAL: Nose
# ELAGRICOLA: Nose
# TODOAGRO: https://www.todoagro.com.ar/feed/
# SUPERCAMPO: https://supercampo.perfil.com/feed/
# AGROVEDAD: Nose
# PERFIL: https://www.perfil.com/canales-rss
# INFOBAE: https://www.infobae.com/arc/outboundfeeds/rss/

# SETTINGS -----------------------------------------

DAYS_BACK = 1  # 🔵 How many days back to search (1 = yesterday only, 2 = last two days, etc.)


RSS_FEEDS = [
# LA NACION
    "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",
# CLARIN
    "https://www.clarin.com/rss/lo-ultimo/",
    "https://www.clarin.com/rss/politica/",
    "https://www.clarin.com/rss/mundo/",
    "https://www.clarin.com/rss/sociedad/",
    "https://www.clarin.com/rss/policiales/",
    "https://www.clarin.com/rss/ciudades/",
    "https://www.clarin.com/rss/opinion/",
    "https://www.clarin.com/rss/cartas_al_pais/",
    "https://www.clarin.com/rss/cultura/",
    "https://www.clarin.com/rss/rural/",
    "https://www.clarin.com/rss/economia/",
    "https://www.clarin.com/rss/tecnologia/",
    "https://www.clarin.com/rss/internacional/",
    "https://www.clarin.com/rss/revista-enie/",
    "https://www.clarin.com/rss/viva/",
    "https://www.clarin.com/rss/br/",
    "https://www.clarin.com/rss/deportes/",
    "https://www.clarin.com/rss/espectaculos/tv/",
    "https://www.clarin.com/rss/espectaculos/cine/",
    "https://www.clarin.com/rss/espectaculos/musica/",
    "https://www.clarin.com/rss/espectaculos/teatro/",
    "https://www.clarin.com/rss/espectaculos/",
    "https://www.clarin.com/rss/autos/",
    "https://www.clarin.com/rss/buena-vida/",
    "https://www.clarin.com/rss/viajes/",
    "https://www.clarin.com/rss/arq/",
# INFOCAMPO
    "https://www.infocampo.com.ar/feed/",
# BICHOS DE CAMPO
    "https://www.infocampo.com.ar/feed/",
# VALOR SOJA
    "https://www.valorsoja.com/feed/",
# TODO AGRO
    "https://www.todoagro.com.ar/feed/",
# SUPER CAMPO
    "https://supercampo.perfil.com/feed/",
# PERFIL
    "https://www.perfil.com/feed",
    "https://www.perfil.com/rss/politica",
    "https://www.perfil.com/rss/economia",
    "https://www.perfil.com/rss/sociedad",
    "https://www.perfil.com/rss/deportes",
    "https://www.perfil.com/rss/internacional",
    "https://www.perfil.com/rss/espectaculos",
    "https://www.perfil.com/rss/cultura",
    "https://www.perfil.com/rss/tecnologia",
    "https://www.perfil.com/rss/salud",
    "https://www.perfil.com/rss/agro",
    "https://www.perfil.com/rss/autos",
# INFOBAE
    "https://www.infobae.com/arc/outboundfeeds/rss/"
]

# FUNCTIONS -----------------------------------------

def normalize_text(text):
    """
    Normalize text: remove accents and lowercase.
    """
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.lower()

# TIME WINDOW ----------------------------------------

now = datetime.now()
today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)

start_date = (now - timedelta(days=DAYS_BACK)).replace(hour=0, minute=0, second=0, microsecond=0)
end_date = today_9am

print(f"Filtering news from {start_date} to {end_date}")

# SCRAPE & FILTER ----------------------------------------

grouped_news = {}

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)
    source_title = feed.feed.title if "title" in feed.feed else "Fuente desconocida"

    for entry in feed.entries:
        try:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        except AttributeError:
            continue

        if start_date <= published_time <= end_date:
            title = entry.title
            link = entry.link

            try:
                summary_text = entry.summary
            except AttributeError:
                summary_text = ""

            if any(
                normalize_text(keyword) in normalize_text(title) or
                normalize_text(keyword) in normalize_text(summary_text)
                for keyword in KEYWORDS
            ):
                if source_title not in grouped_news:
                    grouped_news[source_title] = []
                grouped_news[source_title].append((title, link, published_time))

# BUILD EMAIL BODY ----------------------------------------

email_body = "<h2>🌾 Resumen Diario de Noticias Agro 🌾</h2>\n"
email_body += f"<p>🗓️ Noticias de los últimos {DAYS_BACK} día(s) (desde {start_date.strftime('%d/%m/%Y %H:%M')} hasta {end_date.strftime('%d/%m/%Y %H:%M')})</p>\n"

for source, articles in grouped_news.items():
    email_body += f"<h3>🔵 {source}</h3>\n<ul>"
    # Sort articles by date
    articles.sort(key=lambda x: x[2])
    for title, link, published_time in articles:
        article_date = published_time.strftime('%d/%m %H:%M')
        email_body += f"<li>📰 [{article_date}] <a href='{link}' target='_blank'>{title}</a></li>\n"
    email_body += "</ul>\n"

email_body += "<hr><p style='font-size:small;color:gray;'>Email generado automáticamente - Proyecto RSS Agro News 🇦🇷</p>"

# CREATE AND SEND EMAIL ----------------------------------------

msg = MIMEText(email_body, "html")
msg["Subject"] = f"🌾 Noticias Agro - {datetime.now().strftime('%d/%m/%Y')}"
msg["From"] = SENDER_EMAIL
msg["To"] = RECIPIENT_EMAIL

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print("✅ Email sent successfully!")
