import os
import pika
import json
import time
import couchdb
import requests

from dotenv import load_dotenv

load_dotenv()
couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')
quests_db = couch['quests']
jobs_db = couch['jobs']

apiKey = os.getenv('API_KEY')
if not apiKey:
    print(" [!] WARNING: API_KEY environment variable is not set.")

def call_gemini_ai(prompt):
    if not apiKey:
        return "Помилка: API ключ не встановлено в системних змінних (API_KEY)."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={apiKey}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    for delay in [1, 2, 4, 8, 16]:
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"AI API Error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"AI Connection error: {e}")
            time.sleep(delay)
    return "Вибачте, ШІ не зміг проаналізувати відповіді зараз."

def process_task(ch, method, properties, body):
    try:
        task_data = json.loads(body)
        job_id = task_data['job_id']

        if job_id not in jobs_db:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        job = jobs_db[job_id]

        job['status'] = 'PROCESSING'
        doc_id, doc_rev = jobs_db.save(job)
        job['_rev'] = doc_rev

        filled_data = job['data']
        all_quests = [quests_db[id] for id in quests_db]
        original_quest = next((q for q in all_quests if q.get('title') == job.get('quest_title')), None)

        if not original_quest:
            job['status'] = 'ERROR'
            jobs_db.save(job)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        results = []
        score = 0
        analysis_prompt = "Ти асистент викладача. Проаналізуй відповіді студента на тест. Для кожної помилки поясни, чому відповідь неправильна і як відповісти правильно.\n\n"

        for i, q_filled in enumerate(filled_data['question_list']):
            correct_q = original_quest['question_list'][i]
            is_correct = q_filled['answer'] == correct_q['correct_answers']
            results.append(is_correct)
            if is_correct:
                score += 1
            else:
                analysis_prompt += f"Питання: {correct_q['question']}\nВідповідь студента: {q_filled['answer']}\nПравильна відповідь: {correct_q['correct_answers']}\n---\n"

        ai_explanation = "Всі відповіді правильні! Чудова робота."
        if score < len(results):
            ai_explanation = call_gemini_ai(analysis_prompt)

        latest_job = jobs_db[job_id]
        latest_job['status'] = 'DONE'
        latest_job['score'] = score
        latest_job['result'] = {
            "correctness": results,
            "ai_analysis": ai_explanation
        }

        jobs_db.save(latest_job)
        print(f" [x] Job {job_id} processed successfully. Score: {score}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [!] Unexpected error: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    credentials = pika.PlainCredentials('myuser', 'mypassword')
    parameters = pika.ConnectionParameters(
        host='127.0.0.1',
        port=5672,
        credentials=credentials,
        virtual_host='/'
    )

    while True:
        try:
            print(' [*] Connecting to RabbitMQ (Port 5672)...')
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='ai_tasks', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='ai_tasks', on_message_callback=process_task)

            print(' [*] Worker is waiting for tasks. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print(" [!] Connection failed. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f" [!] Unexpected error: {e}")
            break

if __name__ == "__main__":
    start_worker()