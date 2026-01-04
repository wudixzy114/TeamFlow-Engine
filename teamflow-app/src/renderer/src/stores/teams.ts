import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {api} from '@/api';
import {useAuthStore} from "@/stores/auth";
import {toast} from 'vue-sonner';

export const useTeamsStore = defineStore('teams', () => {
  // --- State ---
  const myTeams = ref<Team[]>([]);
  const currentTeamId = ref<string | null>(null);
  const currentTeamDetail = ref<TeamDetail | null>(null);
  const teamSkillTree = ref<SkillTreeData | null>(null); // 新增：团队技能树

  const authStore = useAuthStore();
  const router = useRouter();
  const myInvitations = ref<InvitationRecord[]>([]);
  const initialFetchDone = ref(false);
  const isLoadingDetail = ref(false);

  // --- Getters ---
  const hasTeams = computed(() => myTeams.value.length > 0);
  const selectedTeam = computed(() => myTeams.value.find(team => team.id === currentTeamId.value));
  const isCurrentUserOwner = computed(() => {
    if (!authStore.user || !currentTeamDetail.value) return false;
    return authStore.user.id === currentTeamDetail.value.owner.id;
  });

  // --- Actions ---

  async function fetchMyTeams() {
    try {
      const simpleTeamsData = await api.teams.listMyTeams();

      if (simpleTeamsData.length === 0) {
        myTeams.value = [];
        currentTeamId.value = null;
        currentTeamDetail.value = null;
        return;
      }

      // 获取所有团队的成员详情（用于填充 owner 完整信息，因为 listMyTeams 可能只返回简化信息）
      // 注意：如果 listMyTeams 已经返回了正确的 owner User 对象，这步可以简化
      const detailPromises = simpleTeamsData.map(team => api.teams.listMember(team.id));
      const memberDetails = await Promise.all(detailPromises);

      myTeams.value = simpleTeamsData.map((team, index) => ({
        id: team.id,
        name: team.name,
        owner: memberDetails[index].owner,
      }));

      // 自动选择逻辑
      if (myTeams.value.length > 0 && !myTeams.value.some(t => t.id === currentTeamId.value)) {
        // 当前选中的团队不在列表里（可能被踢了），选第一个
        await setCurrentTeam(myTeams.value[0].id);
      } else if (myTeams.value.length > 0 && currentTeamId.value) {
        // 刷新当前团队详情
        await fetchCurrentTeamDetail();
      }

    } catch (error) {
      console.error('Failed to fetch my teams:', error);
      // 如果获取列表失败，重置状态
      myTeams.value = [];
      currentTeamId.value = null;
      currentTeamDetail.value = null;
    } finally {
      initialFetchDone.value = true;
    }
  }

  async function setCurrentTeam(teamId: string) {
    currentTeamId.value = teamId;
    await fetchCurrentTeamDetail();
  }

  /**
   * 获取当前选中团队的详细信息
   */
  async function fetchCurrentTeamDetail() {
    if (!currentTeamId.value) {
      currentTeamDetail.value = null;
      teamSkillTree.value = null;
      return;
    }

    isLoadingDetail.value = true;

    try {
      // 1. 获取成员列表
      const baseTeam = myTeams.value.find(t => t.id === currentTeamId.value);
      if (!baseTeam) {
        // 理论上不应该发生，除非 sync 还没完成
        throw new Error(`Team with ID ${currentTeamId.value} not found locally.`);
      }

      const membersData = await api.teams.listMember(currentTeamId.value);

      currentTeamDetail.value = {
        id: baseTeam.id,
        name: baseTeam.name,
        owner: baseTeam.owner,
        members: membersData.members,
      };

      // 2. 顺便获取团队技能树（可选，也可以单独放到一个 Action）
      try {
        teamSkillTree.value = await api.teams.getTeamSkillTree(currentTeamId.value);
      } catch (e) {
        // 技能树获取失败不影响团队详情显示
        console.warn('Failed to fetch skill tree', e);
        teamSkillTree.value = null;
      }

    } catch (error) {
      console.error('Failed to fetch team detail:', error);
      currentTeamDetail.value = null;
      teamSkillTree.value = null;
    } finally {
      isLoadingDetail.value = false;
    }
  }

  async function kickMember(memberId: string): Promise<boolean> {
    if (!currentTeamId.value) return false;
    try {
      await api.teams.kickTeamMember(currentTeamId.value, {id: memberId});
      toast.success('成员已移除');
      await fetchCurrentTeamDetail();
      return true;
    } catch (error) {
      console.error('Failed to kick member:', error);
      return false;
    }
  }

  async function transferOwnership(newOwnerId: string): Promise<boolean> {
    if (!currentTeamId.value) return false;
    try {
      await api.teams.changeTeamOwner(currentTeamId.value, {id: newOwnerId});
      toast.success('群主转让成功');
      await fetchMyTeams(); // 需要刷新列表更新 Owner 信息
      return true;
    } catch (error) {
      console.error('Failed to transfer ownership:', error);
      return false;
    }
  }

  async function leaveCurrentTeam(): Promise<boolean> {
    if (!currentTeamId.value || isCurrentUserOwner.value) return false;
    try {
      await api.teams.leaveTeam(currentTeamId.value);
      toast.success('已退出团队');
      // 退出后清理当前 ID
      currentTeamId.value = null;
      await fetchMyTeams();
      if (myTeams.value.length === 0) {
        await router.replace('/');
      } else {
        await setCurrentTeam(myTeams.value[0].id);
      }
      return true;
    } catch (error) {
      console.error('Failed to leave team:', error);
      return false;
    }
  }

  async function fetchAllMyInvites() {
    try {
      myInvitations.value = await api.teams.listAllMyInvites();
    } catch (error) {
      console.error('Failed to fetch my invitations:', error);
      myInvitations.value = [];
    }
  }

  async function acceptInvite(code: string): Promise<boolean> {
    try {
      await api.teams.acceptInvitation({code});
      toast.success('加入团队成功！');
      await fetchMyTeams();
      await fetchAllMyInvites(); // 刷新邀请列表（移除已接受的）
      return true;
    } catch (error) {
      console.error('Failed to accept invitation:', error);
      toast.error('加入失败，验证码可能已过期');
      return false;
    }
  }

  async function declineInvite(code: string): Promise<boolean> {
    try {
      await api.teams.declineInvitation({code});
      toast.success('已拒绝邀请');
      myInvitations.value = myInvitations.value.filter(invite => invite.invite_code !== code);
      return true;
    } catch (error) {
      console.error('Failed to decline invitation:', error);
      toast.error('操作失败');
      return false;
    }
  }

  async function createTeam(payload: TeamCreate): Promise<boolean> {
    try {
      await api.teams.createTeam(payload);
      toast.success('团队创建成功！');
      await fetchMyTeams();
      // 自动切换到新创建的团队（如果后端能返回 ID 最好，这里只能重新 fetch 后取最后一个或者靠用户选）
      // 假设新创建的在最后，或者用户手动切
      return true;
    } catch (error) {
      console.error('Failed to create team:', error);
      toast.error('创建失败');
      return false;
    }
  }

  async function disbandCurrentTeam(): Promise<boolean> {
    if (!currentTeamId.value || !isCurrentUserOwner.value) return false;
    try {
      await api.teams.deleteTeam(currentTeamId.value);
      toast.success('团队已解散');
      currentTeamId.value = null;
      await fetchMyTeams();
      if (myTeams.value.length === 0) {
        await router.replace('/');
      } else {
        await setCurrentTeam(myTeams.value[0].id);
      }
      return true;
    } catch (error) {
      console.error('Failed to disband team:', error);
      return false;
    }
  }

  async function sendInvitation(email_user: string): Promise<boolean> {
    if (!currentTeamId.value) return false;
    try {
      await api.teams.inviteMember(currentTeamId.value, {email_username: email_user});
      toast.success('邀请已发送');
      return true;
    } catch (error) {
      console.error('Failed to send invitation:', error);
      toast.error('邀请发送失败，请检查用户名或邮箱');
      return false;
    }
  }

  async function updateTeamName(newName: string): Promise<boolean> {
    if (!currentTeamId.value || !isCurrentUserOwner.value) return false;
    try {
      await api.teams.modifyTeam(currentTeamId.value, {name: newName});
      toast.success('团队名称已更新');

      // 乐观更新
      if (currentTeamDetail.value) currentTeamDetail.value.name = newName;
      const teamInList = myTeams.value.find(t => t.id === currentTeamId.value);
      if (teamInList) teamInList.name = newName;

      return true;
    } catch (error) {
      console.error('Failed to update team name:', error);
      return false;
    }
  }

  function resetState() {
    myTeams.value = [];
    currentTeamId.value = null;
    currentTeamDetail.value = null;
    teamSkillTree.value = null;
    myInvitations.value = [];
    initialFetchDone.value = false; // 重置为 false，下次登录会重新 fetch
    isLoadingDetail.value = false;
  }

  return {
    // State
    myTeams,
    currentTeamId,
    currentTeamDetail,
    myInvitations,
    teamSkillTree,
    initialFetchDone,
    isLoadingDetail,
    // Getters
    hasTeams,
    selectedTeam,
    isCurrentUserOwner,
    // Actions
    fetchMyTeams,
    fetchAllMyInvites,
    acceptInvite,
    declineInvite,
    createTeam,
    setCurrentTeam,
    fetchCurrentTeamDetail,
    kickMember,
    transferOwnership,
    leaveCurrentTeam,
    disbandCurrentTeam,
    sendInvitation,
    updateTeamName,
    resetState
  };
}, {
  persist: {
    pick: ['currentTeamId']
  }
});
