import {defineStore} from 'pinia';
import {ref, watch} from 'vue';
import {api} from '@/api';
import {useTeamsStore} from './teams';
import {toast} from 'vue-sonner';
import type {AxiosError} from 'axios'; // 引入 AxiosError 用于类型断言

export const useCharterStore = defineStore('charter', () => {
  const teamsStore = useTeamsStore();

  // --- State ---
  const charter = ref<Charter | null>(null);
  const isLoading = ref(false);
  const isEditing = ref(false);

  // --- Actions ---

  async function fetchCharter() {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) {
      charter.value = null;
      return;
    }

    isLoading.value = true;
    try {
      charter.value = await api.charter.getCharter(teamId);
    } catch (error) {
      const err = error as AxiosError;
      // 404 表示该团队还没有创建公约，属于正常业务流程，不报错
      if (err.response?.status === 404) {
        charter.value = null;
      } else {
        console.error('Failed to fetch team charter:', error);
        toast.error('获取团队公约失败');
      }
    } finally {
      isLoading.value = false;
    }
  }

  async function saveCharter(content: string) {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return;

    isLoading.value = true;
    try {
      // API 期望格式: { content: string }
      await api.charter.updateCharter(teamId, {content});
      toast.success('公约已更新！');
      isEditing.value = false;
      // 重新获取以确保前端数据（如 update_time, update_by）与后端同步
      await fetchCharter();
    } catch (error) {
      console.error('Failed to save team charter:', error);
      toast.error('保存失败，请稍后再试');
    } finally {
      isLoading.value = false;
    }
  }

  // 删除公约
  async function removeCharter() {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return;

    try {
      await api.teams.deleteCharter(teamId);
      charter.value = null;
      toast.success('公约已删除');
    } catch (error) {
      console.error('Failed to delete charter:', error);
      toast.error('删除失败');
    }
  }

  function enterEditMode() {
    isEditing.value = true;
  }

  function cancelEditMode() {
    isEditing.value = false;
  }

  // 监听团队 ID 变化，自动重新获取
  watch(
    () => teamsStore.currentTeamId,
    (newTeamId) => {
      if (newTeamId) {
        isEditing.value = false;
        fetchCharter();
      } else {
        charter.value = null;
      }
    },
    {immediate: true}
  );

  return {
    charter,
    isLoading,
    isEditing,
    fetchCharter,
    saveCharter,
    removeCharter,
    enterEditMode,
    cancelEditMode,
  };
});
