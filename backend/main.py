from typing import List

import couchdb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

import uvicorn

from starlette import status
from starlette.responses import JSONResponse

class Question(BaseModel):
    title: str
    question: str
    answers: List[str]
    correct_answers: str


class Quest(BaseModel):
    title: str
    date: str
    question_list: List[Question]
    author: str

# QUEST_LIST: List[Quest] = []
# USERS = {
#     "admin": "1234",
#     "test": "test"
# }

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#http://LOGIN:PASSWORD@127.0.0.1:5984/
couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')

if 'quests' not in couch:
    quests_db = couch.create('quests')
else:
    quests_db = couch['quests']

if 'users' not in couch:
    users_db = couch.create('users')
    users_db.save({'_id': 'admin', 'password': '1234'})
    users_db.save({'_id': 'test', 'password': 'test'})
else:
    users_db = couch['users']

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

@app.post("/create-quest")
async def create_quest(quest: Quest):
    try:
        quests_db.save(jsonable_encoder(quest))
        return JSONResponse(
            {
                "success": True,
            }
        )
    except:
        return JSONResponse(
            {
                "success": False,
            }
        )

@app.get("/get-quest-list")
async def get_quest_list():
    try:
        quest_list = [quests_db[doc_id] for doc_id in quests_db]
        return JSONResponse({
            "quest_list": quest_list,
        })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.get("/get-quest")
async def get_quest(quest_id: int):
    try:
        quest_list = [quests_db[doc_id] for doc_id in quests_db]

        if 0 <= quest_id < len(quest_list):
            q = quest_list[quest_id]
            return JSONResponse({
                "title": q.get("title"),
                "date": q.get("date"),
                "question_list": q.get("question_list", []),
                "author": q.get("author"),
            })
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.post("/login")
async def login(data: LoginRequest):
    if data.username in users_db:
        user_doc = users_db[data.username]
        if user_doc.get("password") == data.password:
            return {"success": True, "user": {"username": data.username}}
    return {"success": False}

@app.post("/check-quest")
async def check_quest(quest: FilledQuest):
    empty_quest = None
    quest_list = [quests_db[doc_id] for doc_id in quests_db]

    for q in quest_list:
        if q.get("title") == quest.title and q.get("author") == quest.author:
            empty_quest = q
            break

    if empty_quest is None:
        return JSONResponse({"success": False, "error": "Quest not found"})

    answer_list = []
    correct_questions = empty_quest.get("question_list", [])

    for i, correct_question in enumerate(correct_questions):
        if quest.question_list[i].answer == correct_question.get("correct_answers"):
            answer_list.append(True)
        else:
            answer_list.append(False)

    score = sum(answer_list)

    return JSONResponse({
        "success": True,
        "correctness": answer_list,
        "score": score,
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
