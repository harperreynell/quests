import os
import jwt
import pika
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import couchdb
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

import uvicorn

from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Схема для отримання токена з заголовка Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')
quests_db = couch['quests'] if 'quests' in couch else couch.create('quests')
users_db = couch['users'] if 'users' in couch else couch.create('users')
jobs_db = couch['jobs'] if 'jobs' in couch else couch.create('jobs')

def get_rabbitmq_channel():
    try:
        credentials = pika.PlainCredentials('myuser', 'mypassword')
        parameters = pika.ConnectionParameters(
            host='127.0.0.1',
            port=5672,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='ai_tasks', durable=True)
        return connection, channel
    except Exception as e:
        print(f"RabbitMQ connection error: {e}")
        return None, None

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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Спроба декодувати токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print(" [!] Auth Error: Token payload missing 'sub'")
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        print(" [!] Auth Error: Token has expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        print(f" [!] Auth Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/login")
async def login(data: LoginRequest):
    if data.username in users_db:
        user_doc = users_db[data.username]
        if user_doc.get("password") == data.password:
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
    except:
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
    job_id = str(uuid.uuid4())
    job_data = {
        "_id": job_id,
        "status": "QUEUED",  # Встановлюємо QUEUED одразу
        "user": username,
        "quest_title": quest_filled.title,
        "data": jsonable_encoder(quest_filled),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Спочатку зберігаємо один раз статус QUEUED
    jobs_db.save(job_data)

    # Тільки ПІСЛЯ успішного збереження публікуємо в чергу
    conn, ch = get_rabbitmq_channel()
    if ch:
        ch.basic_publish(
            exchange='',
            routing_key='ai_tasks',
            body=json.dumps({"job_id": job_id}),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
        return {"success": True, "job_id": job_id}
    else:
        return {"success": False, "error": "Broker unavailable"}

@app.get("/get-job-status/{job_id}")
async def get_job_status(job_id: str):
    if job_id in jobs_db:
        job = jobs_db[job_id]
        return {
            "status": job.get("status"),
            "result": job.get("result"),
            "score": job.get("score")
        }
    raise HTTPException(status_code=404)

# New meth for My Quests
@app.delete("/delete-quest/{doc_id}")
async def delete_quest(doc_id: str):
    try:
        doc = quests_db[doc_id]
        quests_db.delete(doc)
        return JSONResponse({"success": True})
    except Exception as e:
        print(e)
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
        print(e)
        return JSONResponse({"success": False, "error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)