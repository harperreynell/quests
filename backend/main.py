import os
import jwt
import pika
import json
import uuid
import boto3
import asyncio
import aio_pika
from datetime import datetime, timedelta, timezone
from typing import List, Dict

import couchdb
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

import uvicorn
from starlette import status
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# Завантаження змінних оточення
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', "your-super-long-secret-key-fallback-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- Бази даних та Сховище ---
couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')
quests_db = couch['quests'] if 'quests' in couch else couch.create('quests')
users_db = couch['users'] if 'users' in couch else couch.create('users')
jobs_db = couch['jobs'] if 'jobs' in couch else couch.create('jobs')

# Ініціалізація S3 (MinIO)
s3_client = boto3.client(
    's3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1'
)
BUCKET_NAME = 'quiz-results'

# --- WebSocket Менеджер ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f" [+] WebSocket connected: {user_id}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f" [-] WebSocket disconnected: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f" [!] Error sending WS message to {user_id}: {e}")

manager = ConnectionManager()

# --- RabbitMQ Логіка ---
def get_rabbitmq_channel():
    try:
        credentials = pika.PlainCredentials('myuser', 'mypassword')
        parameters = pika.ConnectionParameters(host='127.0.0.1', port=5672, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='ai_tasks', durable=True)
        channel.queue_declare(queue='job_updates', durable=True)
        return connection, channel
    except Exception as e:
        print(f" [!] RabbitMQ Sync connection error: {e}")
        return None, None

# Фонова задача для прослуховування черги оновлень
async def consume_job_updates():
    while True:
        try:
            print(" [*] Background listener: Attempting to connect to RabbitMQ...")
            connection = await aio_pika.connect_robust(
                "amqp://myuser:mypassword@127.0.0.1:5672/"
            )
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("job_updates", durable=True)
                print(" [*] Background listener: Connected and waiting for job updates.")

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            data = json.loads(message.body.decode())
                            job_id = data.get("job_id")
                            status_val = data.get("status")
                            user_id = data.get("user")

                            # Якщо воркер не надіслав user_id, шукаємо в базі
                            if not user_id and job_id in jobs_db:
                                user_id = jobs_db[job_id].get("user")

                            print(f" [x] Processing update: Job {job_id} -> {status_val} (User: {user_id})")

                            # Якщо задача готова, збираємо всі дані для фронтенду
                            if status_val == "DONE" and job_id:
                                try:
                                    if job_id in jobs_db:
                                        job_doc = jobs_db[job_id]
                                        # Підтягуємо фінальний результат з бази
                                        data["score"] = job_doc.get("score")
                                        data["result"] = job_doc.get("result", {})

                                        # Підтягуємо текст аналізу з S3
                                        s3_key = data["result"].get("s3_key")
                                        if s3_key:
                                            s3_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                                            data["result"]["ai_analysis"] = s3_obj['Body'].read().decode('utf-8')
                                except Exception as e:
                                    print(f" [!] Error enriching DONE message: {e}")

                            if user_id:
                                await manager.send_personal_message(data, user_id)
                            else:
                                print(f" [?] Could not find recipient for job {job_id}")
        except Exception as e:
            print(f" [!!] Update listener crashed: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_job_updates())

# --- Моделі ---
class Question(BaseModel):
    title: str
    question: str
    answers: List[str]
    correct_answers: str

class Quest(BaseModel):
    title: str
    date: str
    question_list: List[Question]

class LoginRequest(BaseModel):
    username: str
    password: str

class FilledQuestion(BaseModel):
    title: str
    question: str
    answer: str

class FilledQuest(BaseModel):
    title: str
    date: str
    question_list: List[FilledQuestion]
    author: str

# --- JWT Helpers ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- Ендпоінти ---
@app.post("/login")
async def login(data: LoginRequest):
    if data.username in users_db and users_db[data.username].get("password") == data.password:
        token = create_access_token(data={"sub": data.username})
        return {"success": True, "access_token": token, "user": {"username": data.username}}
    return {"success": False}

@app.post("/create-quest")
async def create_quest(quest: Quest, username: str = Depends(get_current_user)):
    try:
        quest_data = jsonable_encoder(quest)
        quest_data["author"] = username
        quests_db.save(quest_data)
        return {"success": True}
    except Exception:
        return {"success": False}

@app.get("/get-quest-list")
async def get_quest_list():
    quest_list = [quests_db[doc_id] for doc_id in quests_db]
    return {"quest_list": quest_list}

@app.get("/get-quest")
async def get_quest(quest_id: int):
    quest_list = [quests_db[doc_id] for doc_id in quests_db]
    if 0 <= quest_id < len(quest_list):
        return quest_list[quest_id]
    raise HTTPException(status_code=404)

@app.post("/check-quest")
async def check_quest(quest_filled: FilledQuest, username: str = Depends(get_current_user)):
    print(f" [+] Check-quest request from: {username}")
    job_id = str(uuid.uuid4())
    job_data = {
        "_id": job_id,
        "status": "QUEUED",
        "user": username,
        "quest_title": quest_filled.title,
        "data": jsonable_encoder(quest_filled),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    jobs_db.save(job_data)

    conn, ch = get_rabbitmq_channel()
    if ch:
        # Передаємо username, щоб бекенд міг ідентифікувати власника при оновленні
        ch.basic_publish(
            exchange='',
            routing_key='ai_tasks',
            body=json.dumps({"job_id": job_id, "user": username}),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
        return {"success": True, "job_id": job_id}
    return {"success": False, "error": "Broker unavailable"}

# --- WebSocket Ендпоінт ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(username, websocket)
    try:
        while True:
            # Чекаємо пінг або дані від клієнта для підтримки з'єднання
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(username, websocket)
    except Exception:
        manager.disconnect(username, websocket)

@app.get("/get-job-status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404)

    job = jobs_db[job_id]
    result = job.get("result", {})

    if job.get("status") == "DONE" and result and "s3_key" in result:
        try:
            s3_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=result["s3_key"])
            ai_analysis = s3_obj['Body'].read().decode('utf-8')
            result["ai_analysis"] = ai_analysis
        except Exception:
            result["ai_analysis"] = "Помилка завантаження детального звіту з S3."

    return {"status": job.get("status"), "result": result, "score": job.get("score")}

# CRUD операції для квізів
@app.delete("/delete-quest/{doc_id}")
async def delete_quest(doc_id: str):
    try:
        doc = quests_db[doc_id]
        quests_db.delete(doc)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.put("/update-quest/{doc_id}")
async def update_quest(doc_id: str, quest: Quest):
    try:
        doc = quests_db[doc_id]
        doc["title"] = quest.title
        doc["date"] = quest.date
        doc["question_list"] = jsonable_encoder(quest.question_list)
        quests_db.save(doc)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)