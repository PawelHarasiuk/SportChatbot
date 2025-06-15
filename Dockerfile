FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh
#RUN  chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
