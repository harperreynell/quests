from fastapi.testclient import TestClient
import main
import uuid
import asyncio

client = TestClient(main.app)


def unique_title():
    return "test_" + str(uuid.uuid4())


class FakeUsers:
    def __contains__(self, key):
        return key == "test"

    def __getitem__(self, key):
        return {"password": "test"}


class FakeUsersFail:
    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        return {"password": "wrong"}


class FakeDBError:
    def __iter__(self):
        raise Exception("DB error")


def test_login_unit_success():
    main.users_db = FakeUsers()

    result = asyncio.run(
        main.login(main.LoginRequest(username="test", password="test"))
    )

    assert result["success"] is True


def test_login_unit_fail_wrong_password():
    main.users_db = FakeUsersFail()

    result = asyncio.run(
        main.login(main.LoginRequest(username="test", password="test"))
    )

    assert result["success"] is False


def test_login_unit_user_not_found():
    class Empty:
        def __contains__(self, key):
            return False

    main.users_db = Empty()

    result = asyncio.run(
        main.login(main.LoginRequest(username="nope", password="test"))
    )

    assert result["success"] is False


def test_create_quest_success(monkeypatch):
    class FakeDB:
        def save(self, data):
            return True

    monkeypatch.setattr(main, "quests_db", FakeDB())

    data = {
        "title": "T",
        "date": "2026",
        "author": "me",
        "question_list": []
    }

    r = client.post("/create-quest", json=data)

    assert r.json()["success"] is True


def test_create_quest_fail(monkeypatch):
    class FakeDB:
        def save(self, data):
            raise Exception()

    monkeypatch.setattr(main, "quests_db", FakeDB())

    data = {
        "title": "T",
        "date": "2026",
        "author": "me",
        "question_list": []
    }

    r = client.post("/create-quest", json=data)

    assert r.json()["success"] is False


def test_get_quest_list_error(monkeypatch):
    monkeypatch.setattr(main, "quests_db", FakeDBError())

    r = client.get("/get-quest-list")

    assert r.status_code == 400


def test_get_quest_out_of_range(monkeypatch):
    class FakeDB:
        def __iter__(self):
            return iter([])

        def __getitem__(self, key):
            return {}

    monkeypatch.setattr(main, "quests_db", FakeDB())

    r = client.get("/get-quest?quest_id=10")

    assert r.status_code == 400


def test_check_quest_partial_correct(monkeypatch):
    class FakeDB:
        def __iter__(self):
            return iter(["1"])

        def __getitem__(self, key):
            return {
                "title": "T",
                "author": "me",
                "question_list": [
                    {"correct_answers": "4"},
                    {"correct_answers": "5"}
                ]
            }

    monkeypatch.setattr(main, "quests_db", FakeDB())

    r = client.post("/check-quest", json={
        "title": "T",
        "date": "2026",
        "author": "me",
        "question_list": [
            {"title": "Q1", "question": "", "answer": "4"},
            {"title": "Q2", "question": "", "answer": "0"}
        ]
    })

    assert r.json()["score"] == 1


def test_check_quest_not_found_unit(monkeypatch):
    class FakeDB:
        def __iter__(self):
            return iter([])

        def __getitem__(self, key):
            return {}

    monkeypatch.setattr(main, "quests_db", FakeDB())

    r = client.post("/check-quest", json={
        "title": "X",
        "date": "2026",
        "author": "me",
        "question_list": []
    })

    assert r.json()["success"] is False


def test_real_flow():
    title = unique_title()

    create_data = {
        "title": title,
        "date": "2026",
        "author": "me",
        "question_list": [
            {
                "title": "Q1",
                "question": "2+2",
                "answers": ["3", "4"],
                "correct_answers": "4"
            }
        ]
    }

    client.post("/create-quest", json=create_data)

    r = client.post("/check-quest", json={
        "title": title,
        "date": "2026",
        "author": "me",
        "question_list": [
            {"title": "Q1", "question": "", "answer": "4"}
        ]
    })

    assert r.json()["score"] == 1


def test_login_contract():
    r = client.post("/login", json={
        "username": "test",
        "password": "test"
    })

    data = r.json()

    assert "success" in data
    assert isinstance(data["success"], bool)


def test_check_quest_contract():
    r = client.post("/check-quest", json={
        "title": "none",
        "date": "2026",
        "author": "me",
        "question_list": []
    })

    assert "success" in r.json()