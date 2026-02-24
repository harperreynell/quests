<template>
  <div class="container">
  <div class="page" @click="activeQuestion = null">
    <div class="quest-header" @click.stop>
      <input
          v-model="quest.title"
          placeholder="Quest Title"
          class="title-input"
      />
    </div>

    <div class="questions">

      <div
          v-for="(q, qi) in quest.question_list"
          :key="qi"
          class="question-card"
          :class="{ active: activeQuestion === qi }"
          @click.stop="setActive(qi)"
      >

        <div
            class="card-preview"
            v-if="activeQuestion !== qi"
        >
          <h3>{{ q.title || "Untitled Question" }}</h3>
          <p class="preview-text">
            {{ q.question || "Click to edit this question..." }}
          </p>
        </div>

        <div
            v-else
            class="card-expanded"
            @click.stop
        >

          <div class="card-header" @click="setActive(qi)">
            <h3>{{ q.title || "Untitled Question" }}</h3>
            <span class="arrow">▲</span>
          </div>

          <div class="card-body">
            <input
                v-model="q.title"
                placeholder="Question Title"
                class="q-title"
                @click.stop
            />

            <textarea
                v-model="q.question"
                placeholder="Full question..."
                @click.stop
            ></textarea>

            <h4>Answers</h4>

            <div
                v-for="(a, ai) in q.answers"
                :key="ai"
                class="answer-row"
            >
              <input
                  v-model="q.answers[ai]"
                  placeholder="Answer"
                  @click.stop
                  class="input-answer"
              />
              <button
                  class="small"
                  @click.stop="removeAnswer(qi, ai)"
              >
                ✕
              </button>
            </div>

            <button
                class="secondary"
                @click.stop="addAnswer(qi)"
            >
              + Add Answer
            </button>

            <select
                v-model="q.correct_answers"
                class="correct-input"
                @click.stop
            >
              <option disabled value="">Select Correct Answer...</option>
              <option
                  v-for="(a, ai) in q.answers"
                  :key="ai"
                  :value="a"
                  :disabled="!a.trim()"
              >
                {{ a ? a : `Empty Option ${ai + 1}` }}
              </option>
            </select>

            <button
                class="danger"
                @click.stop="removeQuestion(qi)"
            >
              Delete Question
            </button>
          </div>
        </div>
      </div>
    </div>

    <button
        class="add-question-btn"
        @click.stop="addQuestion"
    >
      ＋
    </button>

    <button
        class="primary submit"
        @click.stop="submitQuest"
    >
      Create Quest
    </button>

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

      this.activeQuestion = this.quest.question_list.length - 1;
    },

    removeQuestion(index) {
      this.quest.question_list.splice(index, 1);

      if (this.activeQuestion === index) {
        this.activeQuestion = null;
      }
    },

    addAnswer(qIndex) {
      this.quest.question_list[qIndex].answers.push("");
    },

    removeAnswer(qIndex, aIndex) {
      this.quest.question_list[qIndex].answers.splice(aIndex, 1);
    },

    setActive(i) {
      this.activeQuestion = this.activeQuestion === i ? null : i;
    },

    async submitQuest() {
      if (!this.quest.title.trim()) {
        alert("You need to add a title for the quest.");
        return;
      }

      if (this.quest.question_list.length === 0) {
        alert("You need to add at least one question to the quest.");
        return;
      }

      for (let i = 0; i < this.quest.question_list.length; i++) {
        const q = this.quest.question_list[i];

        if (!q.correct_answers.trim()) {
          this.activeQuestion = i;
          alert(`You need to add a correct answer for Question ${i + 1}.`);
          return;
        }

        if (q.answers.length === 0) {
          this.activeQuestion = i;
          alert(`You need to add at least one answer option for Question ${i + 1}.`);
          return;
        }
      }

      let today = new Date();
      let dd = String(today.getDate()).padStart(2, '0');
      let mm = String(today.getMonth() + 1).padStart(2, '0');
      let yyyy = today.getFullYear();

      today = mm + '/' + dd + '/' + yyyy;
      this.quest.date = today

      const questId = this.$route.params.id;
      const url = questId
          ? `http://localhost:8000/update-quest/${questId}`
          : "http://127.0.0.1:8000/create-quest";

      const method = questId ? "PUT" : "POST";

      const res = await fetch(url, {
        method: method,
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(this.quest)
      });

      const data = await res.json();
      this.message = data.success
          ? (questId ? "Quest updated successfully." : "Quest created successfully.")
          : "Failed to save quest";

      if (data.success && !questId) {
        this.quest.title = "";
        this.quest.question_list = [];
        this.activeQuestion = null;
      }
    },
  },
  async created() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (user) {
      this.quest.author = user.username;
    } else {
      this.$router.push("/login");
      return;
    }

    const questId = this.$route.params.id;
    if (questId) {
      const res = await fetch('http://localhost:8000/get-quest-list');
      const data = await res.json();
      const existingQuest = data.quest_list.find(q => q._id === questId);

      if (existingQuest) {
        this.quest = existingQuest;
      }
    }
  }
};
</script>

<style>
.container {
  width: 100%;
  //display: flex;
  justify-content: center;
  align-items: flex-start;
  background: #0b0f14;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}


.page {
  max-width: 1100px;
  margin: 40px auto;
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, serif;
  color: #e5e7eb;
}

.quest-header {
  background: #111827;
  padding: 20px;
  display: flex;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin: 20px;
  border: 1px solid #1f2937;
}

.title-input {
  width: 100%;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #030712;
  color: #e5e7eb;
}

.input-answer {
  margin-top: 8px;
  background: #030712;
  border: 1px solid #1f2937;
  color: #e5e7eb;
  padding: 8px;
  border-radius: 8px;
}

.questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-card {
  background: #111827;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.05s ease, border 0.1s ease;
  border: 1px solid #1f2937;
}

.question-card:hover {
  transform: translateY(-1px);
}

.question-card.active {
  border: 1px solid #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.3);
}

.card-preview {
  padding: 16px;
}

.card-preview h3 {
  margin: 0 0 6px 0;
  color: #e5e7eb;
}

.preview-text {
  color: #9ca3af;
  margin: 0;
}

.card-expanded {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding-bottom: 8px;
  border-bottom: 1px solid #1f2937;
}

.arrow {
  color: #9ca3af;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.q-title {
  flex: 1;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #030712;
  color: #e5e7eb;
}

textarea {
  min-height: 80px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  padding: 8px;
  background: #030712;
  color: #e5e7eb;
}

.answer-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.correct-input {
  margin-top: 8px;
  background: #030712;
  border: 1px solid #1f2937;
  color: #e5e7eb;
  padding: 8px;
  border-radius: 8px;
}

.add-question-btn {
  display: block;
  margin: 20px auto;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  font-size: 28px;
  background: #2563eb;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.add-question-btn:hover {
  background: #1d4ed8;
}

.primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
}

.secondary {
  background: #1f2937;
  color: #e5e7eb;
  border: none;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
}

.danger {
  background: #7f1d1d;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
}

.small {
  background: #1f2937;
  color: #e5e7eb;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.submit {
  display: block;
  margin: 20px auto;
}

.msg {
  text-align: center;
  font-weight: 500;
  color: #34d399;
}
</style>
