import {defineStore} from 'pinia';
import {ref, watch} from 'vue';
import {api} from '@/api';
import {useTeamsStore} from './teams';
import {toast} from 'vue-sonner';

type Period = 'day' | 'week' | 'month';

export const useDashboardStore = defineStore('dashboard', () => {
  const teamsStore = useTeamsStore();

  // --- State ---
  const period = ref<Period>('week');
  const compassData = ref<CompassData | null>(null);
  const focusTimeData = ref<FocusTimeData | null>(null);
  const insightsData = ref<AIInsights | null>(null);
  const isLoading = ref(false);

  // --- Actions ---

  function setPeriod(newPeriod: Period) {
    if (period.value === newPeriod) return;
    period.value = newPeriod;
    fetchAllDashboardData();
  }

  async function fetchAllDashboardData() {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return;

    isLoading.value = true;
    try {
      // 使用 Promise.all 并行请求数据，提高加载速度
      const [compass, focus, insights] = await Promise.all([
        api.dashboard.getCompassData(teamId, period.value),
        api.dashboard.getFocusTimeData(teamId, period.value),
        api.dashboard.getInsightsData(teamId, period.value)
      ]);

      compassData.value = compass;
      focusTimeData.value = focus;
      insightsData.value = insights;
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('数据看板加载失败，部分数据可能不可用');
      // 失败时可以保留旧数据，也可以清空，视需求而定。这里选择不强制清空，防止闪烁。
    } finally {
      isLoading.value = false;
    }
  }

  // --- Watcher ---
  watch(
    () => teamsStore.currentTeamId,
    (newTeamId, oldTeamId) => {
      // 仅当 ID 真正改变且有效时才重新请求
      if (newTeamId && newTeamId !== oldTeamId) {
        // 重置数据，提供加载反馈
        compassData.value = null;
        focusTimeData.value = null;
        insightsData.value = null;
        fetchAllDashboardData();
      }
    },
    {immediate: true}
  );

  return {
    period,
    compassData,
    focusTimeData,
    insightsData,
    isLoading,
    setPeriod,
    fetchAllDashboardData,
  };
});
