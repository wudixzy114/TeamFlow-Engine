import {defineStore} from 'pinia';
import {ref, watch} from 'vue';
import {api} from '@/api';
import {useTeamsStore} from './teams';
import {toast} from 'vue-sonner';

export const useFlowSessionStore = defineStore('flowSession', () => {
  const teamsStore = useTeamsStore();

  // --- State ---
  // 修正类型：列表返回的是 FlowSession (带 ID), 不是 FlowSessionCreate
  const sessionHistory = ref<FlowSession[]>([]);
  const isLoading = ref(false);

  // --- Actions ---

  /**
   * 获取当前团队的专注记录历史
   */
  async function fetchSessionHistory() {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) {
      sessionHistory.value = [];
      return;
    }

    isLoading.value = true;
    try {
      const data = await api.flowSessions.listFlowSessions(teamId);
      sessionHistory.value = data.sort((a, b) =>
        new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
      );
    } catch (error) {
      console.error('Failed to fetch flow session history:', error);
      sessionHistory.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 提交一个新的专注记录
   */
  async function submitFlowSession(sessionData: FlowSessionCreate) {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) {
      toast.error('请先选择一个团队');
      return;
    }

    isLoading.value = true;
    try {
      await api.flowSessions.createFlowSession(teamId, sessionData);
      toast.success('专注记录已提交！');
      await fetchSessionHistory();
    } catch (error) {
      console.error('Failed to submit flow session:', error);
      toast.error('提交失败，请稍后再试');
    } finally {
      isLoading.value = false;
    }
  }

  // 删除记录
  async function removeSession(sessionId: string) {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return;

    if (!window.confirm('确定要删除这条专注记录吗？')) return;

    try {
      await api.flowSessions.deleteFlowSession(teamId, {id: sessionId});
      sessionHistory.value = sessionHistory.value.filter(s => s.id !== sessionId);
      toast.success('删除成功');
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('删除失败');
    }
  }

  watch(() => teamsStore.currentTeamId, (newTeamId) => {
    if (newTeamId) {
      fetchSessionHistory();
    }
  }, {immediate: true});

  return {
    sessionHistory,
    isLoading,
    fetchSessionHistory,
    submitFlowSession,
    removeSession
  };
});
