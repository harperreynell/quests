<template>
  <div class="container">
    <div class="page" v-if="quest">
      <div class="quest-header">
        <h1>{{ quest.title }}</h1>
        <p>Author: {{ quest.author }}</p>
        <p>Date: {{ quest.date }}</p>
      </div>
      <div
          v-for="(q, qi) in quest.question_list"
          :key="qi"
          class="question-card"
      >
        <h3>{{ q.title }}</h3>
        <p>{{ q.question }}</p>

        <div
            v-for="(answer, ai) in q.answers"
            :key="ai"
            class="answer-option"
        >
          <label>
            <input
                type="radio"
                :name="'question-' + qi"
                :value="answer"
                v-model="filled_answers[qi]"
            />
            {{ answer }}
          </label>
        </div>
      </div>

      <button class="primary submit-button" @click="submitQuest">
        Submit Answers
      </button>

      <div v-if="result" class="result-box">
        <h3>Score: {{ result.score }} / {{ quest.question_list.length }}</h3>
        <p
            v-for="(c, i) in result.correctness"
            :key="i"
        >
          Question {{ i + 1 }}:
          <span :style="{ color: c ? '#34d399' : '#ef4444' }">
            {{ c ? "Correct" : "Wrong" }}
          </span>
        </p>
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
      result: null
    };
  },

  async created() {
    const id = this.$route.params.id;

    const res = await fetch(
        `http://localhost:8000/get-quest?quest_id=${id}`
    );

    this.quest = await res.json();

    this.filled_answers = new Array(
        this.quest.question_list.length
    ).fill("");
  },

  methods: {
    async submitQuest() {
      const user = JSON.parse(localStorage.getItem("user"));

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

      const res = await fetch(
          "http://localhost:8000/check-quest",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(filledQuest)
          }
      );

      this.result = await res.json();
    }
  }
};
</script>

<style scoped>
.question-card {
  background: #111827;
  padding: 24px;
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px solid #1f2937;
  align-items: center;
  display: flex;
  justify-content: center;
  flex-direction: column;
  width: 50%;
  margin-left: 25%;
}

.answer-option {
  margin: 6px 0;
}

.result-box {
  margin-top: 20px;
  padding: 20px;
  background: #111827;
  border-radius: 16px;
  align-items: center;
  display: flex;
  justify-content: center;
  flex-direction: column;
  width: 50%;
  margin-left: 25%;
}

.quest-header {
  align-items: center;
  display: flex;
  justify-content: center;
  flex-direction: column;
  width: 50%;
  margin-top: 24px;
  padding: 24px;
  margin-left: 25%;
}

.submit-button {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-left: 45%
}
</style>