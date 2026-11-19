FROM node:24-bookworm-slim AS angular-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-railway.txt
COPY backend/ ./
COPY --from=angular-build /build/frontend/dist/careerbridge/browser/ ./angular_dist/
RUN python manage.py collectstatic --noinput
ENV DJANGO_SETTINGS_MODULE=config.railway_settings
CMD ["sh", "/app/start-railway.sh"]
