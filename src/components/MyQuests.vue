<template>
  <div class="container">
    <div class="page">
      <h1 class="heading">My Quests</h1>
      <div
          v-for="q in my_quests"
          :key="q._id"
          class="quest-card"
      >
        <h3>{{ q.title }}</h3>
        <p>Date: {{ q.date }}</p>
        <p>Questions: {{ q.question_list.length }}</p>

        <div style="margin-top: 16px; display: flex; gap: 10px;">
          <button class="primary" @click.stop="editQuest(q._id)">Edit</button>
          <button class="danger" @click.stop="deleteQuest(q._id)">Delete</button>
        </div>
      </div>
      <p v-if="my_quests.length === 0">You haven't created any quests yet.</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      my_quests: []
    }
  },
  methods: {
    async getMyQuests()
    {
      try
      {
        const res = await fetch('http://localhost:8000/get-quest-list');
        const data = await res.json();

        const user = JSON.parse(localStorage.getItem("user"));

        if (user && data.quest_list)
        {
          this.my_quests = data.quest_list.filter(q => q.author === user.username);
        }
      } catch (error)
      {
        console.error("Error:", error);
      }
    },
    editQuest(id) {
      this.$router.push(`/edit-quest/${id}`);
    },
    async deleteQuest(id) {
      if (!confirm("Are you sure you want to delete this quest?")) return;

      const res = await fetch(`http://localhost:8000/delete-quest/${id}`, {
        method: "DELETE"
      });
      const data = await res.json();

      if (data.success) {
        this.getMyQuests();
      } else {
        alert("Failed to delete quest.");
      }
    }
  },
  created() {
    this.getMyQuests();
  }
}
</script>

<style scoped>
.heading { font-size: 50px; }
.quest-card {
  background: #111827;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid #1f2937;
  width: 100%;
  padding: 24px;
  margin-bottom: 24px;
}
</style>