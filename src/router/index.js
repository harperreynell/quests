import { createRouter, createWebHistory } from "vue-router";

import Home from "../components/Home.vue";
import CreateQuest from "../components/CreateQuest.vue";

const routes = [
    {
        path: "/",
        name: "Home",
        component: Home
    },
    {
        path: "/home",
        name: "HomeExplicit",
        component: Home
    },
    {
        path: "/create-quest",
        name: "CreateQuest",
        component: CreateQuest
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

export default router;
