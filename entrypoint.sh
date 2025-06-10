#!/bin/bash
set -e
if [ -z "$SERVICE" ]; then
  echo "ERROR: Zmienna SERVICE nie ustawiona. Użyj SERVICE=scraper, SERVICE=rag lub SERVICE=backend"
  exit 1
fi

# Pierwsze uruchomienie tuż po starcie kontenera
if [ "$SERVICE" = "scraper" ]; then
  echo "[`date`] Initial scrape"
  python /app/scrapper/scrap.py || echo "Pierwszy scraping zakończony błędem"
elif [ "$SERVICE" = "rag" ]; then
  echo "[`date`] Initial RAG update"
  python /app/run_rag_update.py || echo "Pierwszy run_rag_update błędny"
elif [ "$SERVICE" = "backend" ]; then
  echo "[`date`] Starting Flask backend"
  # Uruchamiamy backend i wychodzimy z entrypoint (Flask sam działa w foreground)
  python /app/backend/app.py
  # Po uruchomieniu Flask, proces się nie zakończy, więc entrypoint zostaje przy życiu.
  exit 0
else
  echo "Unknown SERVICE: $SERVICE"
  exit 1
fi

# Pętla tylko dla scraper i rag; backend już wystartowany i zakończył entrypoint
while true; do
  if [ "$SERVICE" = "scraper" ]; then
    echo "[`date`] Running scraper..."
    python /app/scrapper/scrap.py || echo "Scraper error"
  elif [ "$SERVICE" = "rag" ]; then
    echo "[`date`] Running RAG update..."
    python /app/run_rag_update.py || echo "RAG update error"
  fi
  sleep 600
done
