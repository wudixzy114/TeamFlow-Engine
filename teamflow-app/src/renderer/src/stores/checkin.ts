import {defineStore} from 'pinia';
import {ref, watch} from 'vue';
import {api} from '@/api';
import {useTeamsStore} from './teams';
import {toast} from 'vue-sonner';

export const useCheckinStore = defineStore('checkin', () => {
  const teamsStore = useTeamsStore();

  // --- State ---
  // 使用 Record 缓存各团队当天的签到状态: { "team_id_1": true, "team_id_2": false }
  const checkinStatus = ref<Record<string, boolean>>({});
  const isLoading = ref(false);

  // --- Getters ---
  /**
   * 判断当前团队今日是否已签到
   * 如果没有选定团队或数据未加载，默认为 true (避免未加载完成时弹出签到框)，直到数据加载完成
   */
  const hasCurrentTeamCheckedIn = (): boolean => {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return true;

    // 如果状态是 undefined，说明还没请求过 API，暂时返回 true 保持安静
    return checkinStatus.value[teamId] ?? true;
  };

  // --- Actions ---

  /**
   * 检查当前团队今天的签到状态
   * @param force - 是否强制刷新（忽略缓存）
   */
  async function checkStatusForCurrentTeam(force = false) {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) return;

    // 缓存策略：如果状态已存在且不强制刷新，则直接返回
    if (!force && checkinStatus.value[teamId] !== undefined) {
      return;
    }

    isLoading.value = true;
    try {
      const {has_checked_in} = await api.checkins.checkTodayStatus(teamId);
      checkinStatus.value[teamId] = has_checked_in;
    } catch (error) {
      console.error("Failed to check today's check-in status:", error);
      // 这里不弹窗报错，因为这是静默检查。
      // 如果失败，不要设为 true/false，让它保持 undefined 或之前的状态
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 提交签到
   * @param checkinData - 符合 CheckinCreate 接口的数据
   */
  async function submitCheckin(checkinData: CheckinCreate) {
    const teamId = teamsStore.currentTeamId;
    if (!teamId) {
      toast.error("未选择团队");
      return;
    }

    isLoading.value = true;
    try {
      await api.checkins.createCheckin(teamId, checkinData);

      toast.success('今日签到成功！🎉');

      // 乐观更新：无需再次请求 API，直接标记该团队今日已签到
      checkinStatus.value[teamId] = true;

    } catch (error) {
      console.error('Failed to submit check-in:', error);
      toast.error('签到提交失败，请稍后再试');
      throw error; // 抛出错误供 UI 处理（如关闭模态框）
    } finally {
      isLoading.value = false;
    }
  }

  // 监听团队切换，自动检查状态
  watch(
    () => teamsStore.currentTeamId,
    (newTeamId) => {
      if (newTeamId) {
        // 切换团队时检查状态，如果缓存中有则直接用，没有则发起请求
        checkStatusForCurrentTeam();
      }
    },
    {immediate: true}
  );

  return {
    isLoading,
    checkinStatus,
    hasCurrentTeamCheckedIn,
    checkStatusForCurrentTeam,
    submitCheckin,
  };
});
