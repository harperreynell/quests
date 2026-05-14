<template>
  <div class="container">
    <div class="login-box">
      <h2>Login</h2>
      <input v-model="username" placeholder="Enter username" class="input" />
      <input v-model="password" type="password" placeholder="Enter password" class="input" />
      <button class="primary" @click="handleLogin">Login</button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      username: "",
      password: "",
      error: ""
    };
  },
  methods: {
    async handleLogin() {
      const res = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          username: this.username,
          password: this.password
        })
      });

      const data = await res.json();

      if (data.success) {
        localStorage.setItem("user", JSON.stringify(data.user));
        localStorage.setItem("token", data.access_token);
        this.$router.push("/home");
      } else {
        this.error = "Invalid credentials";
      }
    }
  }
};
</script>

<style scoped>
.login-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #111827;
  padding: 30px;
  margin: auto;
}
.input {
  width: 300px;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #030712;
  color: #e5e7eb;
}
.error { color: #ef4444; }
</style>