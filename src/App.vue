<script>
export default {
  methods: {
    logout() {
      localStorage.removeItem("user");
      this.$router.push("/login");
    }
  }
}

</script>
<template>
  <div class="app-layout">
    <nav class="navbar">
      <router-link to="/home">Home</router-link>
      <router-link to="/create-quest">Create Quest</router-link>
      <button @click="logout">Logout</button>
    </nav>

    <router-view />
  </div>
</template>

<style>
.app-layout {
  width: 100%;
  min-height: 100vh;
  background: #0b0f14;
  color: #e5e7eb;
}

.navbar {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #111827;
  border-bottom: 1px solid #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, serif;
}

.navbar a {
  color: #e5e7eb;
  text-decoration: none;
}

.navbar a:hover {
  color: #2563eb;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, serif;
  background: #0b0f14;
}
</style>
