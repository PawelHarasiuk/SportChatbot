#!/bin/bash
set -e
if [ -z "$SERVICE" ]; then
  echo "ERROR: Zmienna SERVICE nie ustawiona. Użyj SERVICE=scraper, SERVICE=rag lub SERVICE=backend"
  exit 1
fi

if [ "$SERVICE" = "scraper" ]; then
  echo "[`date`] Initial scrape"
  python /app/scrapper/scrap.py || echo "Pierwszy scraping zakończony błędem"
elif [ "$SERVICE" = "rag" ]; then
  echo "[`date`] Initial RAG update"
  python /app/run_rag_update.py || echo "Pierwszy run_rag_update błędny"
elif [ "$SERVICE" = "backend" ]; then
  echo "[`date`] Starting Flask backend"
  python /app/backend/app.py
  exit 0
  elif [ "$SERVICE" = "frontend" ]; then
    streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
  else
  echo "Unknown SERVICE: $SERVICE"
  exit 1
fi

while true; do
  if [ "$SERVICE" = "scraper" ]; then
    echo "[`date`] Running scraper..."
    python /app/scrapper/scrap.py || echo "Scraper error"
  elif [ "$SERVICE" = "rag" ]; then
    echo "[`date`] Running RAG update..."
    python /app/run_rag_update.py || echo "RAG update error"
  fi
  sleep 86400
done
