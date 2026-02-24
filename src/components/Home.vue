<script>
export default{
  data() {
    return {
      quest_list: [],
      searchQuery: "",
      appliedSearchQuery: ""
    }
  },
  computed: {
    filteredQuests() {
      return this.quest_list.filter(q =>
          q.title.toLowerCase().includes(this.appliedSearchQuery.toLowerCase())
      );
    }
  },
  methods: {
    async getQuest() {
      const res = await fetch('http://localhost:8000/get-quest-list')
      const data = await res.json();
      this.quest_list = data['quest_list'];
    },
    openQuest(quest) {
      const originalIndex = this.quest_list.indexOf(quest);
      this.$router.push(`/quest/${originalIndex}`);
    },

    performSearch() {
      this.appliedSearchQuery = this.searchQuery;

    }
  },
  created() {
    this.getQuest();
  }
}
</script>

<template>
  <div class="container">
    <div class="page">
    <h1 class="heading">Welcome to quiz-it</h1>

      <div class="search-container">
        <input
            v-model="searchQuery"
            @keyup.enter="performSearch"
            placeholder="Search quizzes by title..."
            class="search-input"
        />
        <button class="primary search-btn" @click="performSearch">Search</button>
      </div>

      <div
          v-for="(q, qi) in filteredQuests"
          :key="qi"
          class="quest-card"
          @click="openQuest(q)"
      >
        <h3>{{ q.title }}</h3>
        <p>Author: {{ q.author }}</p>
        <p>Date: {{ q.date }}</p>
        <p>Questions: {{ q.question_list.length }}</p>
      </div>

      <p v-if="filteredQuests.length === 0 && quest_list.length > 0" class="no-results">
        No quizzes found for "{{ searchQuery }}"
      </p>

    </div>
  </div>
</template>

<style scoped>
.heading {
  font-size: 50px;
}

.quest-card {
  background: #111827;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.05s ease, border 0.1s ease;
  border: 1px solid #1f2937;
  //padding-left: 5%;
  //margin-bottom: 5%;
  width: 100%;
  padding: 24px;
  margin-bottom: 24px;
}

.search-container {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #1f2937;
  background: #030712;
  color: #e5e7eb;
  font-size: 16px;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #2563eb;
}

.no-results {
  text-align: center;
  color: #9ca3af;
  font-size: 18px;
  margin-top: 40px;
}

.search-btn {
  padding: 0 24px;
  font-size: 16px;
  border-radius: 12px;
}

</style>