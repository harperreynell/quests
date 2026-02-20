from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

import uvicorn

from starlette import status
from starlette.responses import JSONResponse

QUEST_LIST: List[Quest] = []
USERS = {
    "admin": "1234",
    "test": "test"
}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/create-quest")
async def create_quest(quest: Quest):
    try:
        QUEST_LIST.append(quest)
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

@app.get("/get-quest")
async def get_quest(quest_id: int):
    try:
        return JSONResponse(
            {
                "title": QUEST_LIST[quest_id].title,
                "date": QUEST_LIST[quest_id].date,
                "question_list": [
                    {
                        "title": QUEST_LIST[quest_id].question_list[i].title,
                        "question": QUEST_LIST[quest_id].question_list[i].question,
                        "answers": QUEST_LIST[quest_id].question_list[i].answers,
                    } for i in range(len(QUEST_LIST[quest_id].question_list))],
                "author": QUEST_LIST[quest_id].author,
            }
        )
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.get("/get-quest-list")
async def get_quest_list():
    try:
        return JSONResponse({
            "quest_list": jsonable_encoder(QUEST_LIST),
        })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@app.post("/login")
async def login(data: LoginRequest):
    if data.username in USERS and USERS[data.username] == data.password:
        return {"success": True, "user": {"username": data.username}}
    return {"success": False}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
