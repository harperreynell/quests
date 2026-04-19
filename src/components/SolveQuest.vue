<template>
  <div class="container">
    <div class="page" v-if="quest">
      <div class="quest-header">
        <h1>{{ quest.title }}</h1>
        <p>Автор: {{ quest.author }}</p>
      </div>

      <div v-for="(q, qi) in quest.question_list" :key="qi" class="question-card">
        <h3>{{ q.title }}</h3>
        <p>{{ q.question }}</p>
        <div v-for="(answer, ai) in q.answers" :key="ai" class="answer-option">
          <label>
            <input type="radio" :name="'question-' + qi" :value="answer" v-model="filled_answers[qi]" :disabled="job_id" />
            {{ answer }}
          </label>
        </div>
      </div>

      <button v-if="!job_id" class="primary submit-button" @click="submitQuest">
        Відправити на перевірку
      </button>

      <div v-if="job_status" class="status-box">
        <p v-if="job_status !== 'DONE'">Статус: <span class="loading">{{ job_status }}</span></p>

        <div v-if="job_status === 'DONE' && result" class="result-box">
          <h3>Результат: {{ score }} / {{ quest.question_list.length }}</h3>
          <div class="ai-analysis">
            <h4>Аналіз ШІ:</h4>
            <div class="analysis-text">{{ result.ai_analysis }}</div>
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
      job_status: null,
      result: null,
      score: 0,
      pollInterval: null
    };
  },
  async created() {
    const id = this.$route.params.id;
    const res = await fetch(`http://localhost:8000/get-quest?quest_id=${id}`);
    this.quest = await res.json();
    this.filled_answers = new Array(this.quest.question_list.length).fill("");
  },
  methods: {
    async submitQuest() {
      const token = localStorage.getItem("token");
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
        this.startPolling();
      }
    },
    startPolling() {
      this.pollInterval = setInterval(async () => {
        const res = await fetch(`http://localhost:8000/get-job-status/${this.job_id}`);
        const data = await res.json();
        this.job_status = data.status;

        if (data.status === 'DONE') {
          this.result = data.result;
          this.score = data.score;
          clearInterval(this.pollInterval);
        } else if (data.status === 'ERROR') {
          alert("Сталася помилка при обробці");
          clearInterval(this.pollInterval);
        }
      }, 2000);
    }
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
};
</script>

<style scoped>
.question-card { background: #111827; padding: 24px; margin-bottom: 24px; border-radius: 16px; border: 1px solid #1f2937; }
.status-box { margin-top: 20px; text-align: center; }
.loading { color: #fbbf24; font-weight: bold; }
.result-box { background: #111827; padding: 20px; border-radius: 16px; border: 1px solid #34d399; margin-top: 20px; }
.ai-analysis { margin-top: 15px; text-align: left; background: #030712; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb; }
.analysis-text { white-space: pre-wrap; line-height: 1.6; color: #d1d5db; }
.submit-button { display: block; margin: 0 auto; }
.quest-header { text-align: center; margin-bottom: 30px; }
</style>