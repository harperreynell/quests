<template>
  <div class="container">
    <div class="page" v-if="quest">
      <!-- Заголовок квіза -->
      <div class="quest-header">
        <h1>{{ quest.title }}</h1>
        <div class="meta-info">
          <span>Автор: <strong>{{ quest.author }}</strong></span>
          <span>Дата: {{ quest.date }}</span>
        </div>

        <!-- Статус виконання через WebSocket -->
        <div v-if="job_id" class="status-container">
          <span :class="['status-badge', job_status.toLowerCase()]">
            Статус: {{ getStatusTranslation(job_status) }}
          </span>
        </div>
      </div>

      <!-- Список питань -->
      <div class="questions-list">
        <div
            v-for="(q, qi) in quest.question_list"
            :key="qi"
            class="question-card"
            :class="{
              'correct-border': result && result.correctness[qi] === true,
              'wrong-border': result && result.correctness[qi] === false
            }"
        >
          <h3>{{ q.title }}</h3>
          <p class="question-text">{{ q.question }}</p>

          <div class="answers-grid">
            <div
                v-for="(answer, ai) in q.answers"
                :key="ai"
                class="answer-option"
            >
              <label :class="{ 'disabled-label': job_id }">
                <input
                    type="radio"
                    :name="'question-' + qi"
                    :value="answer"
                    v-model="filled_answers[qi]"
                    :disabled="job_id"
                />
                {{ answer }}
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопка відправки -->
      <div class="action-bar" v-if="!job_id">
        <button class="primary submit-button" @click="submitQuest">
          Відправити через WebSocket 🚀
        </button>
      </div>

      <!-- Блок результатів та AI аналізу -->
      <div v-if="job_status === 'DONE'" class="result-section">
        <div class="score-card">
          <h2>Ваш результат: {{ score }} / {{ quest.question_list.length }}</h2>
        </div>

        <div v-if="result && result.ai_analysis" class="ai-box">
          <div class="ai-header">
            <span class="ai-icon">🤖</span>
            <h3>Аналіз від ШІ:</h3>
          </div>
          <div class="ai-content">
            {{ result.ai_analysis }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      quest: null,
      filled_answers: [],
      job_id: null,
      job_status: 'IDLE',
      result: null,
      score: 0,
      socket: null
    };
  },

  async created() {
    const id = this.$route.params.id;
    try {
      const res = await fetch(`http://localhost:8000/get-quest?quest_id=${id}`);
      this.quest = await res.json();
      this.filled_answers = new Array(this.quest.question_list.length).fill("");

      // Ініціалізуємо сокет при вході на сторінку
      this.initWebSocket();
    } catch (e) {
      console.error("Помилка завантаження квізу:", e);
    }
  },

  methods: {
    initWebSocket() {
      const token = localStorage.getItem("token");
      if (!token) return;

      this.socket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Перевіряємо, чи це повідомлення стосується нашої задачі
        if (data.job_id === this.job_id) {
          this.job_status = data.status;

          if (data.status === 'DONE') {
            // Отримуємо збагачені дані (score та ai_analysis) прямо з сокета
            this.result = data.result;
            this.score = data.score;
            console.log("Результат отримано через WS!");
          }
        }
      };

      this.socket.onerror = (err) => console.error("WS Error:", err);
    },

    async submitQuest() {
      const token = localStorage.getItem("token");
      if (!token) {
        alert("Будь ласка, авторизуйтесь.");
        return;
      }

      const filledQuest = {
        title: this.quest.title,
        date: this.quest.date,
        author: this.quest.author,
        question_list: this.quest.question_list.map((q, i) => ({
          title: q.title,
          question: q.question,
          answer: this.filled_answers[i]
        }))
      };

      try {
        const res = await fetch("http://localhost:8000/check-quest", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify(filledQuest)
        });

        const data = await res.json();
        if (data.success) {
          this.job_id = data.job_id;
          this.job_status = 'QUEUED';
        } else {
          alert("Помилка при створенні задачі.");
        }
      } catch (e) {
        console.error("Submit Error:", e);
      }
    },

    getStatusTranslation(status) {
      const map = {
        'IDLE': 'Очікування',
        'QUEUED': 'В черзі',
        'PROCESSING': 'Обробка...',
        'ANALYZING_BY_AI': 'ШІ аналізує помилки...',
        'DONE': 'Завершено ✅'
      };
      return map[status] || status;
    }
  },

  beforeUnmount() {
    if (this.socket) this.socket.close();
  }
};
</script>

<style scoped>
.quest-header {
  text-align: center;
  background: #111827;
  padding: 30px;
  border-radius: 20px;
  border: 1px solid #1f2937;
  margin-bottom: 30px;
}

.meta-info {
  color: #9ca3af;
  margin: 10px 0;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.status-container {
  margin-top: 15px;
}

.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.status-badge.queued { background: #374151; color: #d1d5db; }
.status-badge.processing { background: #1e3a8a; color: #93c5fd; }
.status-badge.analyzing_by_ai { background: #5b21b6; color: #ddd6fe; }
.status-badge.done { background: #064e3b; color: #6ee7b7; }

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.question-card {
  background: #111827;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #1f2937;
  transition: all 0.3s ease;
}

.question-text {
  color: #d1d5db;
  margin-bottom: 15px;
}

.correct-border { border-color: #10b981 !important; }
.wrong-border { border-color: #ef4444 !important; }

.answers-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.answer-option label {
  display: block;
  padding: 10px;
  background: #030712;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
}

.answer-option label:hover {
  background: #1f2937;
}

.disabled-label {
  cursor: default !important;
  opacity: 0.8;
}

.action-bar {
  text-align: center;
  margin-top: 30px;
}

.submit-button {
  padding: 14px 40px;
  font-size: 1.1rem;
  font-weight: bold;
}

.result-section {
  max-width: 800px;
  margin: 40px auto;
}

.score-card {
  text-align: center;
  background: #111827;
  padding: 20px;
  border-radius: 16px;
  border-bottom: 4px solid #2563eb;
}

.ai-box {
  margin-top: 30px;
  background: #0f172a;
  border-radius: 16px;
  padding: 24px;
  border-left: 6px solid #2563eb;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.ai-icon { font-size: 1.5rem; }

.ai-content {
  color: #cbd5e1;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>