<template>
  <div class="container">
    <h1>Create Quest</h1>

    <input v-model="quest.title" placeholder="Quest Title" />
    <input v-model="quest.date" type="date" />
    <input v-model="quest.author" placeholder="Author" />

    <h2>Questions</h2>

    <div v-for="(q, qi) in quest.question_list" :key="qi" class="question-box">
      <input v-model="q.title" placeholder="Question Title" />
      <textarea v-model="q.question" placeholder="Question text"></textarea>

      <h3>Answers</h3>
      <div v-for="(_, ai) in q.answers" :key="ai">
        <input v-model="q.answers[ai]" placeholder="Answer" />
        <button @click="removeAnswer(qi, ai)">X</button>
      </div>

      <button @click="addAnswer(qi)">+ Add Answer</button>

      <input v-model="q.correct_answers" placeholder="Correct Answer" />

      <button @click="removeQuestion(qi)">Remove Question</button>
    </div>

    <button @click="addQuestion">+ Add Question</button>

    <br /><br />
    <button @click="submitQuest">Create Quest</button>

    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: "",
      quest: {
        title: "",
        date: "",
        author: "",
        question_list: []
      }
    };
  },
  methods: {
    addQuestion() {
      this.quest.question_list.push({
        title: "",
        question: "",
        answers: [],
        correct_answers: ""
      });
    },
    removeQuestion(index) {
      this.quest.question_list.splice(index, 1);
    },
    addAnswer(qIndex) {
      this.quest.question_list[qIndex].answers.push("");
    },
    removeAnswer(qIndex, aIndex) {
      this.quest.question_list[qIndex].answers.splice(aIndex, 1);
    },
    async submitQuest() {
      const res = await fetch("http://127.0.0.1:8000/create-quest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.quest)
      });

      const data = await res.json();

      if (data.success) {
        this.message = "Quest created successfully!";
        this.quest = { title: "", date: "", author: "", question_list: [] };
      } else {
        this.message = "Failed to create quest";
      }
    }
  }
};
</script>

<style>
.container {
  max-width: 700px;
  margin: auto;
  font-family: Arial;
}
input, textarea {
  display: block;
  width: 100%;
  margin: 5px 0;
}
.question-box {
  border: 1px solid #ccc;
  padding: 10px;
  margin: 10px 0;
}
button {
  margin: 5px 0;
}
</style>
