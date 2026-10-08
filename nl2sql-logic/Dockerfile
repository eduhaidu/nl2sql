FROM python:3.11

WORKDIR /usr/src/nl2sql-logic

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y libgl1-mesa-glx

RUN uv init

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]