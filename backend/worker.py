import os
import pika
import json
import time
import couchdb
import requests
import boto3

# Підключення до CouchDB
couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')
quests_db = couch['quests']
jobs_db = couch['jobs']

# Налаштування S3 (MinIO)
s3_client = boto3.client(
    's3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
BUCKET_NAME = 'quiz-results'

# Отримання API ключа
apiKey = os.getenv('API_KEY')

def send_update_to_backend(job_id, status, username):
    """Надсилає сигнал бекенду для WebSocket-пуша"""
    try:
        credentials = pika.PlainCredentials('myuser', 'mypassword')
        conn = pika.BlockingConnection(pika.ConnectionParameters(
            host='127.0.0.1', port=5672, credentials=credentials
        ))
        ch = conn.channel()
        ch.queue_declare(queue='job_updates', durable=True)
        ch.basic_publish(
            exchange='',
            routing_key='job_updates',
            body=json.dumps({"job_id": job_id, "status": status, "user": username})
        )
        conn.close()
    except Exception as e:
        print(f" [!] Failed to send WS update to backend: {e}")

def call_gemini_ai(prompt):
    if not apiKey:
        print(" [!] Error: API_KEY environment variable is not set!")
        return "Error: API_KEY is missing."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={apiKey}"

    try:
        res = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # Виводимо помилку в консоль воркера для діагностики
            error_detail = res.text
            print(f" [!] Gemini API Error ({res.status_code}): {error_detail}")
            return f"AI Error: {res.status_code}"
    except Exception as e:
        print(f" [!] AI Request exception: {e}")
        return "AI Connection Error"

def process_task(ch, method, properties, body):
    try:
        data = json.loads(body)
        job_id = data.get('job_id')
        username = data.get('user')

        print(f" [*] Starting Job: {job_id} (User: {username})")

        if job_id not in jobs_db:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        job = jobs_db[job_id]
        job['status'] = 'PROCESSING'
        jobs_db.save(job)

        send_update_to_backend(job_id, "PROCESSING", username)

        # Отримуємо всі квізи для пошуку оригіналу
        all_quests = [quests_db[id] for id in quests_db]
        original = next((q for q in all_quests if q.get('title') == job.get('quest_title')), None)

        if not original:
            print(f" [!] Quest not found for job {job_id}")
            job['status'] = 'ERROR'
            jobs_db.save(job)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        results, score = [], 0
        prompt = "Ти асистент викладача. Проаналізуй відповіді студента. Поясни помилки:\n\n"

        # Порівнюємо відповіді
        filled_list = job['data']['question_list']
        correct_list = original['question_list']

        for i, q in enumerate(filled_list):
            if i >= len(correct_list): break

            correct_answer = correct_list[i]['correct_answers']
            user_answer = q['answer']
            is_ok = user_answer == correct_answer

            results.append(is_ok)
            if is_ok:
                score += 1
            else:
                prompt += f"Питання: {q['question']}\nВідповідь студента: {user_answer}\nПравильна відповідь: {correct_answer}\n---\n"

        send_update_to_backend(job_id, "ANALYZING_BY_AI", username)

        # Викликаємо ШІ тільки якщо є помилки
        if score < len(results):
            print(f" [->] Calling AI for Job {job_id}...")
            ai_text = call_gemini_ai(prompt)
        else:
            ai_text = "Всі відповіді правильні! Чудова робота."

        # Зберігаємо результат у S3
        s3_key = f"{job_id}.txt"
        s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=ai_text.encode('utf-8'))

        # Фінальне оновлення документа в БД
        latest_job = jobs_db[job_id]
        latest_job.update({
            'status': 'DONE',
            'score': score,
            'result': {"correctness": results, "s3_key": s3_key}
        })
        jobs_db.save(latest_job)

        print(f" [x] Job {job_id} completed. Score: {score}/{len(results)}")
        send_update_to_backend(job_id, "DONE", username)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [!] Error processing task: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    try:
        credentials = pika.PlainCredentials('myuser', 'mypassword')
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='127.0.0.1', port=5672, credentials=credentials
        ))
        channel = connection.channel()
        channel.queue_declare(queue='ai_tasks', durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='ai_tasks', on_message_callback=process_task)

        print(' [*] AI Worker is waiting for tasks. Press CTRL+C to exit.')
        if not apiKey:
            print(" [!] WARNING: API_KEY is not set. AI calls will fail.")

        channel.start_consuming()
    except Exception as e:
        print(f" [!] Worker crashed: {e}")

if __name__ == "__main__":
    start_worker()