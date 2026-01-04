import {defineStore} from 'pinia';
import {ref, reactive} from 'vue';
import {api} from '@/api';
import {useAuthStore} from '@/stores/auth';
import {toast} from 'vue-sonner';

export const useSelfInfoStore = defineStore('selfInfo', () => {
  const authStore = useAuthStore();

  // --- State ---
  const user = ref<User | null>(null);
  const editableUser = reactive<Partial<User>>({});

  // --- Actions ---
  /**
   * 获取个人信息
   */
  async function fetchMyInfo() {
    try {
      const response = await api.selfInfo.getSelfInfo();
      user.value = response;
      Object.assign(editableUser, response);
      authStore.setUserInfo(response);
      return true;
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      return false;
    }
  }

  function resetEditableUser() {
    if (user.value) {
      Object.assign(editableUser, user.value);
    }
  }

  /**
   * 更新个人信息（除邮箱）
   */
  async function updateInfo(): Promise<boolean> {
    if (!user.value) return false;

    // 构造 UserInfoUpdate 类型
    const dataToUpdate: ModifyUserInfoRequest = {
      username: editableUser.username,
      nickname: editableUser.nickname,
      age: editableUser.age ? String(editableUser.age) : undefined, // 确保转为字符串或符合后端要求
      gender: editableUser.gender,
      profession: editableUser.profession,
    };

    try {
      await api.selfInfo.updateSelfInfo(dataToUpdate);
      toast.success('个人信息已更新');
      await fetchMyInfo(); // 确保更新后本地数据同步
      return true;
    } catch (error) {
      console.error("Failed to update info:", error);
      toast.error('更新失败');
      resetEditableUser();
      return false;
    }
  }

  /**
   * 发送修改邮箱的验证码
   */
  async function sendVerificationCode(newEmail: string): Promise<void> {
    try {
      await api.selfInfo.updateEmail({new_email: newEmail});
      toast.success('验证码已发送');
    } catch (error) {
      console.error(error);
      toast.error('发送验证码失败');
      throw error;
    }
  }

  /**
   * 验证邮箱修改
   */
  async function verifyEmailUpdate(code: string): Promise<boolean> {
    try {
      await api.selfInfo.emailVerify({code});
      toast.success('邮箱修改成功！');
      // 关键修复：验证成功后，立即拉取最新用户信息，以便 UI 更新
      await fetchMyInfo();
      return true;
    } catch (error) {
      console.error("Email verification failed:", error);
      toast.error('验证失败，验证码可能错误或已过期');
      return false;
    }
  }

  return {
    user,
    editableUser,
    fetchMyInfo,
    resetEditableUser,
    updateInfo,
    sendVerificationCode,
    verifyEmailUpdate,
  };
});
