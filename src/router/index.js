import { createRouter, createWebHistory } from "vue-router";

import Home from "../components/Home.vue";
import CreateQuest from "../components/CreateQuest.vue";
import Login from "../components/Login.vue";
import SolveQuest from "../components/SolveQuest.vue";
import MyQuests from '../components/MyQuests.vue';

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
    },
    {
        path: "/login",
        name: "Login",
        component: Login
    },
    {
        path: "/quest/:id",
        name: "SolveQuest",
        component: SolveQuest
    },
    {
        path: '/my-quests',
        name: 'MyQuests',
        component: MyQuests
    },
    {
        path: '/edit-quest/:id',
        name: 'EditQuest',
        component: CreateQuest
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach((to, from, next) => {
    const publicPages = ["/login"];
    const authRequired = !publicPages.includes(to.path);
    const user = localStorage.getItem("user");

    if (authRequired && !user) {
        return next("/login");
    }

    next();
});

export default router;
