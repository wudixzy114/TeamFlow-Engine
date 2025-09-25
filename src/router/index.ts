import {createRouter, createWebHistory} from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: MainLayout,
            redirect: '/dashboard',
            children: [
                {
                    path: 'dashboard',
                    name: 'Dashboard',
                    component: () => import('@/views/DashBoard.vue'),
                },
                {
                    path: 'achievements',
                    name: 'Achievements',
                    component: () => import('@/views/Achievements.vue'),
                },
            ],
        },
        // { path: '/login', component: () => import('@/views/Login.vue') }, // 占位
    ],
})

export default router