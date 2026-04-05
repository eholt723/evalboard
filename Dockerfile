# Stage 1: build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + bundled frontend
# Mirror the local layout so Path(__file__).parent.parent.parent resolves correctly:
#   local:  evalboard/backend/app/main.py  → 3 up = evalboard/  → frontend/dist = evalboard/frontend/dist
#   docker: /app/backend/app/main.py       → 3 up = /app/       → frontend/dist = /app/frontend/dist
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /build/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
