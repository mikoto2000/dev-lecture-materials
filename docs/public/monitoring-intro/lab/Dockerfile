FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /lab
COPY common.py app.py labctl.py container_start.py notification_sink.py ./
RUN mkdir .state && chown 10001:10001 .state
USER 10001:10001

CMD ["python", "container_start.py"]
