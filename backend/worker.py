import os
import pika
import json
import time
import boto3
import couchdb
import requests

couch = couchdb.Server('http://couchdb:couchdb@127.0.0.1:5984/')
quests_db = couch['quests']
jobs_db = couch['jobs']

s3_client = boto3.client(
    's3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1'
)
BUCKET_NAME = 'quiz-results'

try:
    s3_client.head_bucket(Bucket=BUCKET_NAME)
except:
    s3_client.create_bucket(Bucket=BUCKET_NAME)

apiKey = os.getenv('API_KEY')

def call_gemini_ai(prompt):
    if not apiKey:
        return "Помилка: API ключ не встановлено в системних змінних (API_KEY)."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={apiKey}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

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

def safe_db_update(job_id, update_func):
    """Допоміжна функція для оновлення документа з обробкою конфліктів ревізій"""
    for _ in range(5):
        try:
            job = jobs_db[job_id]
            updated_job = update_func(job)
            jobs_db.save(updated_job)
            return True
        except couchdb.http.ResourceConflict:
            time.sleep(0.5)
            continue
    return False

def process_task(ch, method, properties, body):
    try:
        task_data = json.loads(body)
        job_id = task_data['job_id']

        if job_id not in jobs_db:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        def set_processing(doc):
            doc['status'] = 'PROCESSING'
            return doc

        if not safe_db_update(job_id, set_processing):
            print(f" [!] Failed to update job {job_id} to PROCESSING due to conflicts")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        job = jobs_db[job_id]
        filled_data = job['data']

        all_quests = [quests_db[id] for id in quests_db]
        original_quest = next((q for q in all_quests if q.get('title') == job.get('quest_title')), None)

        if not original_quest:
            def set_error(doc):
                doc['status'] = 'ERROR'
                return doc
            safe_db_update(job_id, set_error)
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

        s3_key = f"{job_id}_analysis.txt"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=ai_explanation.encode('utf-8')
        )

        def set_done(doc):
            doc['status'] = 'DONE'
            doc['score'] = score
            doc['result'] = {
                "correctness": results,
                "s3_key": s3_key
            }
            return doc

        if safe_db_update(job_id, set_done):
            print(f" [x] Job {job_id} processed. Result saved to S3: {s3_key}")
        else:
            print(f" [!] Failed to save DONE status for {job_id}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [!] Unexpected error: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    credentials = pika.PlainCredentials('myuser', 'mypassword')
    parameters = pika.ConnectionParameters(host='127.0.0.1', port=5672, credentials=credentials)

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='ai_tasks', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='ai_tasks', on_message_callback=process_task)
            print(' [*] Worker is waiting for tasks...')
            channel.start_consuming()
        except Exception as e:
            print(f" [!] Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()