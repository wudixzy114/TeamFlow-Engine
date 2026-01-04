import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router';
import {useAuthStore} from '@/stores/auth';
import {useTeamsStore} from '@/stores/teams';

// 路由配置
const routes: Array<RouteRecordRaw> = [
  // {
  //   path: '/',
  //   redirect: '/design', // 暂时重定向到设计系统以便观察
  // },
  // {
  //   path: '/design',
  //   component: () => import('@/tests/DesignSystem.vue'),
  // },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {requiresAuth: false}
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: {requiresAuth: false}
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: {requiresAuth: false}
  },
  {
    path: '/no-team',
    name: 'NoTeam',
    component: () => import('@/views/NoTeam.vue'),
    meta: {requiresAuth: true},
    redirect: {name: 'NoTeamDefault'},

    children: [
      {
        path: '',
        name: 'NoTeamDefault',
        component: () => import('@/views/no-team/NoTeamDefault.vue'),
      },
      {
        path: 'create',
        name: 'CreateTeam',
        component: () => import('@/views/no-team/CreateTeam.vue'),
      },
      {
        path: 'join',
        name: 'JoinTeam',
        component: () => import('@/views/no-team/JoinTeam.vue'),
      },
    ]
  },
  // 主应用布局
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: {requiresAuth: false},
    children: [
      {
        path: '',
        name: 'Home',
        redirect: '/flow-ritual',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/TeamDashboard.vue'),
      },
      {
        path: 'highlights',
        name: 'Highlights',
        component: () => import('@/views/Highlights.vue'),
        meta: {
          immersive: true
        }
      },
      {
        path: 'flow-ritual',
        name: 'FlowRitual',
        component: () => import('@/views/FlowRitual.vue'),
      },
      {
        path: 'kudos-wall',
        name: 'KudosWall',
        component: () => import('@/views/KudosWall.vue'),
      },
      {
        path: 'team-charter',
        name: 'TeamCharter',
        component: () => import('@/views/TeamCharter.vue'),
      },
      {
        path: 'my-weekly-digest',
        name: 'MyWeeklyDigest',
        component: () => import('@/views/MyWeeklyDigest.vue'),
      },
      {
        path: 'team-management',
        name: 'TeamManagement',
        component: () => import('@/views/TeamManagement.vue'),
      },
      {
        path: 'self-info',
        name: 'SelfInfo',
        component: () => import('@/views/SelfInfo.vue'),
      },
      {
        path: 'flow-link',
        name: 'FlowLink',
        component: () => import('@/views/FlowLink.vue'),
      },
      {
        path: 'ai-manager',
        name: 'AiManager',
        component: () => import('@/views/ModelManager.vue')
      },
      {
        path: 'ai-chat',
        name: 'AiChat',
        component: () => import('@/views/ChatPage.vue')
      },
      {
        path: 'skill-tree',
        name: 'SkillTree',
        component: () => import('@/views/SkillTree.vue'),
        meta: {
          immersive: true
        }
      },
      {
        path: 'team-chat',
        name: 'TeamChat',
        component: () => import('@/views/TeamChat.vue')
      },
      {
        path: 'forum',
        name: 'Forum',
        component: () => import('@/views/forum/Forum.vue')
      }
    ]
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// --- 全局前置守卫 (Navigation Guard) ---
router.beforeEach(async (to, _, next) => {
  const authStore = useAuthStore();
  const teamsStore = useTeamsStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isGoingToNoTeamArea = to.matched.some(record => record.name === 'NoTeam') || to.path.startsWith('/no-team');
  // 1. 未登录拦截
  if (requiresAuth && !authStore.isAuthenticated) {
    return next({name: 'Login', query: {redirect: to.fullPath}});
  }

  // 2. 数据预加载：如果已登录，确保团队数据已加载
  if (authStore.isAuthenticated && !teamsStore.initialFetchDone) {
    try {
      await teamsStore.fetchMyTeams();
    } catch (e) {
      console.warn('Initial team fetch failed', e);
    }
  }

  // 3. 登录页回跳逻辑：已登录用户访问 Login -> 根据是否有团队跳转
  if (authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    return next({name: teamsStore.hasTeams ? 'Dashboard' : 'NoTeamDefault'});
  }

  if (authStore.isAuthenticated) {
    const hasTeams = teamsStore.hasTeams;
    if (!hasTeams) {
      if (isGoingToNoTeamArea) {
        return next()
      }
      if (requiresAuth) {
        return next({name: 'NoTeamDefault'});
      }
      return next();
    }
    if (hasTeams) {
      if (to.name === 'NoTeamDefault') {
        return next({name: 'Dashboard'});
      }
    }
  }

  next();
});

export default router;
