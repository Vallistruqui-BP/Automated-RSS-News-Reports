#!/usr/bin/env python3
import argparse
import feedparser
import json
import os
import sys
import time
import unicodedata
from datetime import datetime, timedelta

# You can change them to suit your news coverage preference
KEYWORDS = [
    # GAMING
    "gaming",
    "videojuegos",
    "gamer",
    "eSports",
    "torneos gaming",
    "streamers",
    "Twitch",
    "Steam",
    "PlayStation",
    "Xbox",
    "Nintendo",
    "comunidad gamer",
    "juegos online",

    # GAMBLING
    "apuestas online",
    "casas de apuestas",
    "casino online",
    "juegos de azar",
    "tragamonedas",
    "apuestas deportivas",
    "criptocasinos",
    "betting",
    "Codere",
    "Bplay",
    "Bet365",
    "juego legal",
    "Lotería Nacional",
    "regulación apuestas",

    # ENTREPRENEURSHIP
    "emprendedores",
    "startups",
    "emprender",
    "aceleradoras",
    "incubadoras",
    "rondas de inversión",
    "inversión ángel",
    "unicornio",
    "fintech",
    "capital de riesgo",
    "economía del conocimiento",
    "negocio digital",
    "startup tecnológica",
    "innovación"
]


# You can add as many RSS links as you want provided that said news coverage site has RSS links available
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
    "https://www.infobae.com/arc/outboundfeeds/rss/",
# SEED TODAY
    "https://www.seedtoday.com/rss.xml"
]

def normalize_text(text: str) -> str:
    nk = unicodedata.normalize('NFKD', text)
    return nk.encode('ascii', 'ignore').decode('ascii').lower()

timestamp = datetime.now().strftime("%Y_%m_%d__%H_%M")

def parse_args():
    p = argparse.ArgumentParser(
        description="Fetch multiple RSS feeds, filter by keywords & date, emit JSON."
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument("--since-days", type=int, default=1,
                       help="How many days back to include (default 1).")
    group.add_argument("--since-hours", type=float,
                       help="How many hours back to include (overrides --since-days).")
    p.add_argument("--output", default= f"RSS_FEEDS_{timestamp}.json", 
                       help="Path to write raw JSON.")

    return p.parse_args()

def main():
    args = parse_args()
    now = datetime.now()

    # Determine time window
    if args.since_hours is not None:
        start_date = now - timedelta(hours=args.since_hours)
    else:
        start_date = now - timedelta(days=args.since_days)
    end_date = now

    print(f"⏱ Filtering entries from {start_date.isoformat()} to {end_date.isoformat()}")

    grouped_news = {}

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        source_title = feed.feed.get("title", "Fuente desconocida")

        for entry in feed.entries:
            try:
                published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except AttributeError:
                continue

            if not (start_date <= published_time <= end_date):
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")

            content_to_check = normalize_text(title + " " + summary)
            if any(normalize_text(k) in content_to_check for k in KEYWORDS):
                grouped_news.setdefault(source_title, []).append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": published_time.isoformat()
                })

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(grouped_news, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in grouped_news.values())
    print(f"✅ Wrote {total} news items to {args.output}")

if __name__ == "__main__":
    main()
