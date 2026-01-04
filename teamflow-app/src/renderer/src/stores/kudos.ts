import {defineStore} from 'pinia';
import {ref} from 'vue';
import {api} from '@/api';
import {useTeamsStore} from './teams';
import {toast} from 'vue-sonner';

export const useKudosStore = defineStore('kudos', () => {
  const teamsStore = useTeamsStore();

  // --- State ---
  const receivedKudos = ref<Kudos[]>([]);
  const isLoading = ref(false);

  // --- Actions ---

  /**
   * 获取我收到的所有 Kudos
   */
  async function fetchMyReceivedKudos() {
    isLoading.value = true;
    try {
      const data = await api.kudos.listMyReceivedKudos();
      receivedKudos.value = data.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    } catch (error) {
      console.error('Failed to fetch received kudos:', error);
      toast.error('获取 Kudos 列表失败');
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 发送一张 Kudos 卡
   */
  async function sendKudos(kudosData: Omit<KudosCreate, 'receiver_id'> & { receiver_id: string | null }) {
    const teamId = teamsStore.currentTeamId;

    if (!teamId) {
      toast.error('请先选择一个团队');
      return;
    }
    if (!kudosData.receiver_id) {
      toast.error('请选择一位接收者');
      return;
    }

    const payload: KudosCreate = {
      receiver_id: kudosData.receiver_id,
      card_type: kudosData.card_type,
      message: kudosData.message,
    };

    try {
      await api.kudos.sendKudos(teamId, payload);
      toast.success('Kudos 已成功发送！');
    } catch (error) {
      console.error('Failed to send kudos:', error);
      toast.error('发送失败');
      throw error;
    }
  }

  // 前端排序辅助函数（如果不涉及后端持久化排序，纯前端展示用）
  function updateKudosOrder(newOrderedKudos: Kudos[]) {
    const newOrderIds = new Set(newOrderedKudos.map(k => k.id));
    const unselectedKudos = receivedKudos.value.filter(k => !newOrderIds.has(k.id));
    receivedKudos.value = [...newOrderedKudos, ...unselectedKudos];
  }

  return {
    receivedKudos,
    isLoading,
    fetchMyReceivedKudos,
    sendKudos,
    updateKudosOrder,
  };
});
