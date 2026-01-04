<template>
  <div class="relative w-full h-full flex justify-center p-6 overflow-y-auto scrollbar-hide">

    <!-- 动态背景光效 -->
    <div
      class="fixed top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 blur-[120px] rounded-full pointer-events-none z-0 animate-pulse"></div>

    <div class="w-full max-w-3xl z-10 flex flex-col gap-6 animate-slide-in-fast pb-10">

      <!-- 头部卡片 -->
      <div
        class="glass-panel p-8 flex flex-col sm:flex-row items-center sm:items-start gap-6 relative overflow-hidden group shrink-0">
        <div class="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none"></div>

        <!-- 头像区域 -->
        <div class="relative shrink-0">
          <div
            class="w-24 h-24 rounded-full bg-gradient-to-br from-bg-surface to-bg-card border-2 border-primary/30 flex items-center justify-center shadow-glow-sm group-hover:shadow-glow transition-all duration-500 overflow-hidden">
            <span
              class="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text select-none inline-block"
            >
              {{ avatarInitials }}
            </span>
          </div>
          <div class="absolute bottom-1 right-1 w-5 h-5 bg-bg-card rounded-full flex items-center justify-center">
            <div class="w-3 h-3 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--c-primary),0.8)]"></div>
          </div>
        </div>

        <!-- 名字与 ID -->
        <div class="flex-1 text-center sm:text-left z-10 min-w-0">
          <h2 class="text-3xl font-bold text-text-main mb-1 tracking-tight truncate">
            {{ selfInfoStore.user?.nickname || selfInfoStore.user?.username || 'User' }}
          </h2>
          <div class="flex items-center justify-center sm:justify-start gap-2 text-text-muted text-sm">
            <span class="font-mono opacity-70">UID: {{ selfInfoStore.user?.id?.split('-')[0] }}...</span>
            <button
              class="hover:text-primary transition-colors cursor-pointer shrink-0"
              title="复制完整ID"
              @click="copyId"
            >
              <div class="i-carbon-copy"></div>
            </button>
          </div>
          <div class="mt-4 flex flex-wrap gap-2 justify-center sm:justify-start">
            <span class="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs border border-primary/20 shrink-0">
              {{ selfInfoStore.user?.profession || '探索者' }}
            </span>
            <span class="px-3 py-1 rounded-full bg-bg-surface text-text-muted text-xs border border-border/30 shrink-0">
              Focus & Connection
            </span>
          </div>
        </div>
      </div>

      <!-- 主要表单区域 -->
      <div class="glass-panel p-6 sm:p-8 shrink-0">
        <h3 class="text-lg font-semibold text-text-main mb-6 flex items-center gap-2">
          <div class="i-carbon-user-profile text-primary"></div>
          基本资料
        </h3>

        <div v-if="selfInfoStore.user" class="space-y-1">
          <SettingsField
            v-for="item in editableFields"
            :key="item.key"
            v-model="selfInfoStore.editableUser[item.key]"
            :input-type="item.type"
            :label="item.label"
            :options="item.options"
            @confirm="handleUpdateInfo"
          />

          <div class="h-px bg-gradient-to-r from-transparent via-border/30 to-transparent my-6"></div>

          <!-- 邮箱专用行 -->
          <div
            class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl hover:bg-bg-surface/30 transition-colors group border border-transparent hover:border-white/5">
            <div class="flex flex-col overflow-hidden">
              <span class="text-text-muted text-sm font-medium">绑定邮箱</span>
              <div class="flex items-center gap-2 mt-1">
                <div class="i-carbon-email text-text-muted shrink-0"></div>
                <span class="text-text-main font-mono tracking-wide truncate">
                  {{ selfInfoStore.user.email }}
                </span>
                <span class="text-xs text-primary bg-primary/10 px-1.5 py-0.5 rounded ml-2 shrink-0">已验证</span>
              </div>
            </div>
            <button
              class="mt-4 sm:mt-0 btn-outline text-xs h-9 px-4 opacity-80 hover:opacity-100 group-hover:border-primary/40 shrink-0"
              @click="openEmailDialog"
            >
              更换邮箱
            </button>
          </div>
        </div>

        <div v-else class="space-y-6 animate-pulse">
          <div v-for="i in 4" :key="i" class="h-14 bg-bg-surface/50 rounded-xl w-full"></div>
        </div>
      </div>
    </div>

    <!-- Email Modal -->
    <TransitionRoot :show="emailDialogVisible" appear as="template">
      <Dialog as="div" class="relative z-50" @close="emailDialogVisible = false">
        <TransitionChild
          as="template"
          enter="duration-300 ease-out"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="duration-200 ease-in"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 backdrop-glass"/>
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4 text-center">
            <TransitionChild
              as="template"
              enter="duration-300 ease-out cubic-bezier(0.16, 1, 0.3, 1)"
              enter-from="opacity-0 scale-95 translate-y-4"
              enter-to="opacity-100 scale-100 translate-y-0"
              leave="duration-200 ease-in"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95 translate-y-4"
            >
              <DialogPanel
                class="w-full max-w-md transform overflow-hidden glass-panel p-8 text-left align-middle shadow-2xl border-primary/20 transition-all">
                <DialogTitle as="h3" class="text-xl font-bold text-text-main flex items-center gap-2">
                  <div class="i-carbon-security text-primary text-2xl"></div>
                  安全验证
                </DialogTitle>

                <div class="mt-2">
                  <p class="text-sm text-text-muted">
                    为了保障您的账户安全，修改邮箱需要进行验证码验证。
                  </p>
                </div>

                <div class="mt-6 space-y-5">
                  <div class="space-y-2">
                    <label class="text-xs font-semibold text-text-muted uppercase tracking-wider">新邮箱地址</label>
                    <div class="relative group">
                      <div
                        class="i-carbon-email absolute left-3 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-primary transition-colors"></div>
                      <input
                        v-model="emailForm.new_email"
                        class="input-base pl-10 bg-bg-surface/50 focus:bg-bg-surface transition-colors"
                        placeholder="name@example.com"
                        type="email"
                      />
                    </div>
                  </div>

                  <div class="space-y-2">
                    <label class="text-xs font-semibold text-text-muted uppercase tracking-wider">验证码</label>
                    <div class="flex gap-3">
                      <input
                        v-model="emailForm.code"
                        class="input-base text-center tracking-[0.5em] font-mono text-lg bg-bg-surface/50 focus:bg-bg-surface transition-colors"
                        maxlength="6"
                        placeholder="------"
                        type="text"
                      />
                      <button
                        :disabled="isSendingCode || countdown < 60"
                        class="btn-outline whitespace-nowrap min-w-[120px] text-sm relative overflow-hidden"
                        @click="handleSendCode"
                      >
                        <span class="relative z-10">{{ sendCodeText }}</span>
                        <div
                          v-if="countdown < 60"
                          :style="{ width: `${(countdown / 60) * 100}%` }"
                          class="absolute inset-0 bg-primary/10 transition-all duration-1000 ease-linear origin-left"
                        ></div>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="mt-8 flex justify-end gap-3">
                  <button
                    class="btn-ghost text-sm"
                    type="button"
                    @click="emailDialogVisible = false"
                  >
                    取消
                  </button>
                  <button
                    class="btn-primary px-8"
                    type="button"
                    @click="handleSubmitEmailChange"
                  >
                    确认修改
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive, computed, onUnmounted} from 'vue';
import {useSelfInfoStore} from '@/stores/selfInfo';
import SettingsField from '@/components/self/SettingsField.vue';
import {toast} from 'vue-sonner';
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogPanel,
  DialogTitle,
} from '@headlessui/vue';

const selfInfoStore = useSelfInfoStore();

type UserKeys = 'username' | 'nickname' | 'gender' | 'age' | 'profession';

interface EditableField {
  key: UserKeys;
  label: string;
  type: 'text' | 'number' | 'select';
  options?: { label: string; value: string }[];
}

const editableFields = ref<EditableField[]>([
  {key: 'nickname', label: '昵称', type: 'text'},
  {key: 'username', label: '用户名', type: 'text'},
  {key: 'profession', label: '职业 / 角色', type: 'text'},
  {
    key: 'gender',
    label: '性别',
    type: 'select',
    options: [
      {label: '男', value: '男'},
      {label: '女', value: '女'},
      {label: '保密', value: '不愿透露'},
    ]
  },
  {key: 'age', label: '年龄', type: 'number'},
]);

const emailDialogVisible = ref(false);
const emailForm = reactive({
  new_email: '',
  code: '',
});

const isSendingCode = ref(false);
const countdown = ref(60);
let timer: ReturnType<typeof setInterval> | null = null;

// --- Computed ---
const avatarInitials = computed(() => {
  // 增加兜底逻辑，防止 null 或 empty
  const name = selfInfoStore.user?.nickname || selfInfoStore.user?.username || '?';
  return name.length >= 2 ? name.substring(0, 2).toUpperCase() : name.toUpperCase();
});

const sendCodeText = computed(() => {
  return countdown.value < 60 ? `${countdown.value}s 后重试` : '获取验证码';
});

// --- Lifecycle ---
// 只要组件挂载，强制更新数据
onMounted(async () => {
  await selfInfoStore.fetchMyInfo();
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

// --- Actions ---

const copyId = () => {
  if (selfInfoStore.user?.id) {
    navigator.clipboard.writeText(selfInfoStore.user.id);
    toast.success('用户 ID 已复制到剪贴板');
  }
};

const handleUpdateInfo = async () => {
  await selfInfoStore.updateInfo();
};

const openEmailDialog = () => {
  emailDialogVisible.value = true;
  emailForm.new_email = '';
  emailForm.code = '';
};

const handleSendCode = async () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailForm.new_email || !emailRegex.test(emailForm.new_email)) {
    toast.error('请输入有效的邮箱地址');
    return;
  }

  if (emailForm.new_email === selfInfoStore.user?.email) {
    toast.error('新邮箱不能与当前邮箱相同');
    return;
  }

  isSendingCode.value = true;

  try {
    await selfInfoStore.sendVerificationCode(emailForm.new_email);
    toast.success('验证码已发送');
    countdown.value = 59;
    timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) {
        clearInterval(timer!);
        isSendingCode.value = false;
        countdown.value = 60;
      }
    }, 1000);
  } catch (error) {
    isSendingCode.value = false;
  }
};

const handleSubmitEmailChange = async () => {
  if (!emailForm.code || emailForm.code.length < 4) {
    toast.warning('请输入完整的验证码');
    return;
  }

  const success = await selfInfoStore.verifyEmailUpdate(emailForm.code);
  if (success) {
    emailDialogVisible.value = false;
    countdown.value = 60;
    if (timer) clearInterval(timer);
    isSendingCode.value = false;
  }
};
</script>
