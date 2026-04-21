FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=/app \
	FREEAPI_CURRENT_VERSION=1.0.1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY archives ./archive
COPY home-assistant/addon/freeapi/run.sh /run.sh

RUN chmod +x /run.sh \
	&& chown -R app:app /app /run.sh

USER app

EXPOSE 8000

CMD ["/run.sh"]
