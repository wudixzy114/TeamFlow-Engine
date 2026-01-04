<!-- src/views/teams/TeamSettingsView.vue -->
<template>
  <div class="h-full w-full flex flex-col overflow-hidden">

    <!-- 滚动区域 -->
    <div class="flex-1 overflow-y-auto p-6 md:p-8 scrollbar-hide">

      <!-- 1. Header (左上角，占据全宽) -->
      <header class="w-full flex-shrink-0 animate-slide-in-fast mb-10">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 class="text-h1 mb-1">Team Settings</h1>
            <div class="flex items-center gap-3 text-muted">
              <p>管理团队成员、权限与配置</p>
              <span v-if="teamDetail" class="w-1 h-1 bg-border rounded-full"></span>
              <!-- ID Copy Badge -->
              <div
                v-if="teamDetail"
                class="flex items-center gap-1.5 cursor-pointer hover:text-primary transition-colors group select-none"
                title="点击复制 Team ID"
                @click="copyTeamId"
              >
                <span class="font-mono text-xs opacity-70">ID: {{ teamDetail.id }}</span>
                <span class="i-carbon-copy text-xs opacity-0 group-hover:opacity-100 transition-opacity"></span>
              </div>
            </div>
          </div>

          <!-- Header Action (Rename) -->
          <button v-if="isOwner" class="btn-outline text-sm" @click="modals.rename.open = true">
            <span class="i-carbon-edit"></span>
            重命名团队
          </button>
        </div>
      </header>

      <!-- 2. Main Content (居中显示，限制最大宽度) -->
      <!-- max-w-5xl + mx-auto 实现居中 -->
      <main v-if="teamDetail" class="w-full max-w-5xl mx-auto space-y-8 pb-12 animate-enter"
            style="animation-delay: 100ms">

        <!-- Section: Members List -->
        <section class="glass-panel overflow-hidden flex flex-col">
          <div class="px-6 py-4 border-b border-border/10 bg-surface/30 flex justify-between items-center">
            <h3 class="text-h2 flex items-center gap-2 text-base">
              <span class="i-carbon-collaborate text-primary"></span>
              成员列表
            </h3>
            <span class="text-xs font-mono px-2 py-0.5 rounded bg-surface/50 text-muted">{{
                allMembers.length
              }} Active</span>
          </div>

          <div class="divide-y divide-border/5">
            <div
              v-for="member in allMembers"
              :key="member.id"
              class="p-4 hover:bg-surface/30 transition-colors group"
            >
              <div class="flex items-center justify-between">
                <!-- Info -->
                <div class="flex items-center gap-4">
                  <div
                    :class="member.isOwner ? 'bg-gradient-to-br from-amber-500 to-orange-600' : 'bg-gradient-to-br from-slate-600 to-slate-800'"
                    class="w-10 h-10 rounded-full flex-center text-sm font-bold text-white shadow-inner border border-white/10"
                  >
                    {{ member.username.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-text">{{ member.username }}</span>
                      <span v-if="member.isOwner"
                            class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20">OWNER</span>
                      <span v-if="isMe(member.id)"
                            class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">YOU</span>
                    </div>
                    <div class="text-xs text-muted">{{ member.email }}</div>
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex items-center gap-2">
                  <button
                    class="btn-icon w-8 h-8 rounded-lg hover:bg-surface text-muted hover:text-text transition-colors"
                    title="详细信息"
                    @click="toggleDetail(member.id)"
                  >
                    <span class="i-carbon-information"></span>
                  </button>

                  <!-- Admin Actions -->
                  <template v-if="isOwner && !member.isOwner">
                    <div class="w-px h-4 bg-border/20 mx-1"></div>
                    <button
                      class="btn-icon w-8 h-8 rounded-lg hover:bg-accent/10 text-muted hover:text-accent transition-colors"
                      title="转让管理权"
                      @click="initiateTransfer(member)"
                    >
                      <span class="i-carbon-trophy"></span>
                    </button>
                    <button
                      class="btn-icon w-8 h-8 rounded-lg hover:bg-error/10 text-muted hover:text-error transition-colors"
                      title="移除成员"
                      @click="initiateKick(member)"
                    >
                      <span class="i-carbon-trash-can"></span>
                    </button>
                  </template>
                </div>
              </div>

              <!-- Expanded Details -->
              <div v-if="expandedId === member.id"
                   class="mt-3 ml-14 p-4 bg-bg-main/30 rounded-lg border border-border/10 grid grid-cols-2 gap-4 animate-slide-in-fast">
                <div>
                  <span class="text-[10px] uppercase text-muted tracking-wider">Profession</span>
                  <p class="text-sm text-text mt-0.5">{{ member.profession || 'Not set' }}</p>
                </div>
                <div>
                  <span class="text-[10px] uppercase text-muted tracking-wider">Gender</span>
                  <p class="text-sm text-text mt-0.5">{{ member.gender || 'Not set' }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Section: Invite -->
        <section class="glass-panel p-6 flex flex-col md:flex-row gap-6 items-center relative overflow-hidden">
          <!-- Background Decoration -->
          <div
            class="absolute -right-20 -top-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>

          <div class="flex-1 relative z-10">
            <h3 class="text-h2 text-base flex items-center gap-2 mb-1">
              <span class="i-carbon-send-alt text-accent"></span>
              邀请成员
            </h3>
            <p class="text-sm text-muted">输入用户名或邮箱地址，发送入队邀请。</p>
          </div>

          <div class="w-full md:w-auto flex gap-2 relative z-10">
            <div class="relative w-full md:w-80">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 i-carbon-email text-muted"></span>
              <input
                v-model="inviteInput"
                class="input-base pl-9"
                placeholder="username / email"
                @keyup.enter="handleInvite"
              />
            </div>
            <button :disabled="!inviteInput" class="btn-primary whitespace-nowrap" @click="handleInvite">
              发送邀请
            </button>
          </div>
        </section>

        <!-- Section: Danger Zone -->
        <section class="border border-error/20 bg-error/5 rounded-xl overflow-hidden mt-8">
          <div class="px-6 py-3 border-b border-error/10 bg-error/10 flex items-center gap-2">
            <span class="i-carbon-warning-alt-filled text-error"></span>
            <h3 class="text-sm font-bold text-error">Danger Zone</h3>
          </div>

          <div class="p-6 space-y-6">
            <!-- Leave -->
            <div class="flex items-center justify-between gap-4">
              <div>
                <h4 class="text-sm font-medium text-text">退出团队</h4>
                <p class="text-xs text-muted mt-1">您将失去对该团队所有资源的访问权限。</p>
              </div>
              <button
                :class="{'opacity-50 cursor-not-allowed': isOwner}"
                :disabled="isOwner"
                class="btn-base bg-transparent border border-border text-text hover:border-error hover:text-error text-xs"
                @click="initiateLeave"
              >
                {{ isOwner ? '请先转让权限' : '退出团队' }}
              </button>
            </div>

            <!-- Disband -->
            <div v-if="isOwner" class="pt-6 border-t border-error/10 flex items-center justify-between gap-4">
              <div>
                <h4 class="text-sm font-medium text-text">解散团队</h4>
                <p class="text-xs text-muted mt-1">此操作不可逆。所有数据将被永久删除。</p>
              </div>
              <button
                class="btn-base bg-error text-white hover:bg-error/90 border-none shadow-lg shadow-error/20 text-xs"
                @click="initiateDisband"
              >
                解散团队
              </button>
            </div>
          </div>
        </section>

      </main>

      <!-- Loading State -->
      <div v-else class="flex justify-center items-center h-64">
        <div class="i-carbon-circle-dash animate-spin text-4xl text-primary/50"></div>
      </div>
    </div>

    <!-- === Modals === -->
    <!-- 1. Generic Confirm Modal -->
    <ConfirmModal
      :cancel-text="modals.confirm.cancelText"
      :confirm-text="modals.confirm.confirmText"
      :description="modals.confirm.desc"
      :is-open="modals.confirm.open"
      :title="modals.confirm.title"
      @close="modals.confirm.open = false"
      @confirm="executeConfirmAction"
    />

    <!-- 2. Rename Input Modal -->
    <InputModal
      :default-value="teamDetail?.name"
      :is-open="modals.rename.open"
      description="请输入新的团队名称。"
      placeholder="例如: 核心开发组"
      title="修改团队名称"
      @close="modals.rename.open = false"
      @confirm="handleRename"
    />

  </div>
</template>

<script lang="ts" setup>
import {ref, computed, onMounted, reactive} from 'vue';
import {useTeamsStore} from '@/stores/teams';
import {useAuthStore} from '@/stores/auth';
import {toast} from 'vue-sonner';
import ConfirmModal from '@/components/share/ConfirmModal.vue';
import InputModal from '@/components/share/InputModal.vue';

const teamsStore = useTeamsStore();
const authStore = useAuthStore();

// --- State ---
const inviteInput = ref('');
const expandedId = ref<string | null>(null);

// --- Modal State Manager ---
type ConfirmAction = () => Promise<void>;

const modals = reactive({
  confirm: {
    open: false,
    title: '',
    desc: '',
    confirmText: '确定',
    cancelText: '取消',
    action: null as ConfirmAction | null
  },
  rename: {
    open: false
  }
});

// --- Computed ---
const teamDetail = computed(() => teamsStore.currentTeamDetail);
const isOwner = computed(() => teamsStore.isCurrentUserOwner);
const allMembers = computed(() => {
  if (!teamDetail.value) return [];
  const ownerId = teamDetail.value.owner.id;
  return [...teamDetail.value.members]
    .map(m => ({...m, isOwner: m.id === ownerId}))
    .sort((a, b) => (b.isOwner ? 1 : 0) - (a.isOwner ? 1 : 0));
});

// --- Helpers ---
const isMe = (id: string) => authStore.user?.id === id;

const copyTeamId = () => {
  if (teamDetail.value?.id) {
    navigator.clipboard.writeText(teamDetail.value.id);
    toast.success('ID 已复制');
  }
};

const toggleDetail = (id: string) => {
  expandedId.value = expandedId.value === id ? null : id;
};

// --- Action Initiators ---

const handleRename = async (newName: string) => {
  if (newName !== teamDetail.value?.name) {
    await teamsStore.updateTeamName(newName);
  }
  modals.rename.open = false;
};

const handleInvite = async () => {
  if (!inviteInput.value) return;
  const success = await teamsStore.sendInvitation(inviteInput.value);
  if (success) inviteInput.value = '';
};

const initiateKick = (member: any) => {
  modals.confirm.title = '移除成员';
  modals.confirm.desc = `确定要将 [${member.username}] 移出团队吗？`;
  modals.confirm.confirmText = '移除';
  modals.confirm.cancelText = '取消';
  modals.confirm.action = async () => {
    await teamsStore.kickMember(member.id);
  };
  modals.confirm.open = true;
};

const initiateTransfer = (member: any) => {
  modals.confirm.title = '转让管理权';
  modals.confirm.desc = `确定将管理权转让给 [${member.username}]？您将失去管理员权限。`;
  modals.confirm.confirmText = '确认转让';
  modals.confirm.cancelText = '取消';
  modals.confirm.action = async () => {
    await teamsStore.transferOwnership(member.id);
  };
  modals.confirm.open = true;
};

const initiateLeave = () => {
  modals.confirm.title = '退出团队';
  modals.confirm.desc = '确定要退出当前团队吗？';
  modals.confirm.confirmText = '退出';
  modals.confirm.cancelText = '取消';
  modals.confirm.action = async () => {
    await teamsStore.leaveCurrentTeam();
  };
  modals.confirm.open = true;
};

const initiateDisband = () => {
  modals.confirm.title = '🔥 解散团队';
  modals.confirm.desc = '解散团队将永久删除所有数据。确定继续吗？';
  modals.confirm.confirmText = '永久解散';
  modals.confirm.cancelText = '取消';
  modals.confirm.action = async () => {
    await teamsStore.disbandCurrentTeam();
  };
  modals.confirm.open = true;
};

const executeConfirmAction = async () => {
  if (modals.confirm.action) {
    await modals.confirm.action();
  }
  modals.confirm.open = false;
};

onMounted(() => {
  if (teamsStore.currentTeamId) {
    teamsStore.fetchCurrentTeamDetail();
  }
});
</script>
