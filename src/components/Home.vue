<script>
export default{
  data() {
    return {
      quest_list: []
    }
  },
  methods: {
    async getQuest(){
      const res = await fetch('http://localhost:8000/get-quest-list')
      const data = await res.json();
      this.quest_list = data['quest_list'];
    },
    openQuest(index) {
      this.$router.push(`/quest/${index}`);
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
      <div
          v-for="(q, qi) in quest_list"
          :key="qi"
          class="quest-card"
          @click="openQuest(qi)"
      >
        <h3>{{ q.title }}</h3>
        <p>Author: {{ q.author }}</p>
        <p>Date: {{ q.date }}</p>
        <p>Questions: {{ q.question_list.length }}</p>
      </div>
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
</style>