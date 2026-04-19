<template>
  <div class="container">
    <div class="page" @click="activeQuestion = null">
      <div class="quest-header" @click.stop>
        <input v-model="quest.title" placeholder="Quest Title" class="title-input" />
      </div>

      <div class="questions">
        <div v-for="(q, qi) in quest.question_list" :key="qi" class="question-card" :class="{ active: activeQuestion === qi }" @click.stop="setActive(qi)">
          <div class="card-preview" v-if="activeQuestion !== qi">
            <h3>{{ q.title || "Untitled Question" }}</h3>
            <p class="preview-text">{{ q.question || "Click to edit..." }}</p>
          </div>
          <div v-else class="card-expanded" @click.stop>
            <div class="card-header" @click="setActive(qi)">
              <h3>Edit Question</h3>
              <span>▲</span>
            </div>
            <div class="card-body">
              <input v-model="q.title" placeholder="Title" class="q-title" />
              <textarea v-model="q.question" placeholder="Question content"></textarea>
              <div v-for="(a, ai) in q.answers" :key="ai" class="answer-row">
                <input v-model="q.answers[ai]" placeholder="Answer" class="input-answer" />
                <button class="small" @click="removeAnswer(qi, ai)">✕</button>
              </div>
              <button class="secondary" @click="addAnswer(qi)">+ Add Answer</button>
              <select v-model="q.correct_answers" class="correct-input">
                <option disabled value="">Correct Answer...</option>
                <option v-for="a in q.answers" :key="a" :value="a">{{ a }}</option>
              </select>
              <button class="danger" @click="removeQuestion(qi)">Delete</button>
            </div>
          </div>
        </div>
      </div>

      <button class="add-question-btn" @click.stop="addQuestion">＋</button>
      <button class="primary submit" @click.stop="submitQuest">Create Quest</button>
      <p v-if="message" class="msg">{{ message }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: "",
      activeQuestion: null,
      quest: { title: "", date: "", question_list: [] }
    };
  },
  methods: {
    addQuestion() {
      this.quest.question_list.push({ title: "", question: "", answers: [], correct_answers: "" });
      this.activeQuestion = this.quest.question_list.length - 1;
    },
    removeQuestion(i) { this.quest.question_list.splice(i, 1); },
    addAnswer(i) { this.quest.question_list[i].answers.push(""); },
    removeAnswer(qi, ai) { this.quest.question_list[qi].answers.splice(ai, 1); },
    setActive(i) { this.activeQuestion = this.activeQuestion === i ? null : i; },
    async submitQuest() {
      const token = localStorage.getItem("token");
      this.quest.date = new Date().toLocaleDateString();

      const res = await fetch("http://127.0.0.1:8000/create-quest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(this.quest)
      });

      const data = await res.json();
      if (data.success) {
        this.message = "Success!";
        this.quest = { title: "", date: "", question_list: [] };
      } else {
        this.message = "Error: Unauthorized or server error";
      }
    }
  }
};
</script>

<style>
.page { max-width: 1100px; margin: 40px auto; font-family: sans-serif; color: #e5e7eb; }
.quest-header { background: #111827; padding: 20px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #1f2937; }
.title-input, .q-title, textarea, .correct-input, .input-answer { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #1f2937; background: #030712; color: #e5e7eb; margin-top: 5px; }
.question-card { background: #111827; border-radius: 16px; border: 1px solid #1f2937; margin-bottom: 10px; cursor: pointer; padding: 15px; }
.question-card.active { border-color: #2563eb; }
.add-question-btn { display: block; margin: 20px auto; width: 50px; height: 50px; border-radius: 50%; background: #2563eb; color: white; border: none; font-size: 24px; cursor: pointer; }
.primary { background: #2563eb; color: white; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; }
.danger { background: #7f1d1d; color: white; border: none; padding: 8px; border-radius: 8px; cursor: pointer; margin-top: 10px;}
.msg { text-align: center; color: #34d399; margin-top: 10px; }
</style>