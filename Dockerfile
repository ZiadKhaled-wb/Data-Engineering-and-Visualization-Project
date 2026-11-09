# Container for free hosting on Hugging Face Spaces (or any Docker host)
FROM python:3.12-slim
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" PORT=7860
WORKDIR /app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
EXPOSE 7860
CMD gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
