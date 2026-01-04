// src/stores/chat.ts

import {defineStore} from 'pinia';
import {ref, computed} from 'vue';
import {
  getChatMessages,
  sendChatMessage,
  deleteChatMessage,
  uploadChatFile,
} from '@/api/chat';
import {toast} from 'vue-sonner';

export const useChatStore = defineStore('chat', () => {
  // --- State ---
  const messages = ref<TeamChat[]>([]);
  const isLoading = ref(false); // 用于初次加载或加载历史
  const isLoadingHistory = ref(false);
  const isSending = ref(false); // 用于发送消息状态
  const hasMoreHistory = ref(true);

  const activeTeamId = ref<string | null>(null);

  // 轮询控制器
  let pollingInterval: number | null = null;
  const POLLING_RATE = 3000;

  // --- Getters ---

  // 根据 created_at 排序，确保 UI 展示顺序正确（旧在上，新在下）
  const sortedMessages = computed(() => {
    return [...messages.value].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  });

  // 获取列表中最新的消息 ID (用于 after_msg_id - 轮询)
  const newestMsgId = computed(() => {
    if (sortedMessages.value.length === 0) return undefined;
    return sortedMessages.value[sortedMessages.value.length - 1].id;
  });

  // 获取列表中最老的消息 ID (用于 before_msg_id - 加载更多历史)
  const oldestMsgId = computed(() => {
    if (sortedMessages.value.length === 0) return undefined;
    return sortedMessages.value[0].id;
  });

  // --- Actions ---

  const resetState = () => {
    stopPolling();
    messages.value = [];
    isLoading.value = false;
    isLoadingHistory.value = false;
    hasMoreHistory.value = true; // 默认为 true，直到 API 告诉我们没有了
    isSending.value = false;
  };

  /**
   * 切换聊天室并进行初次加载
   */
  const switchChatRoom = async (teamId: string) => {
    if (activeTeamId.value === teamId && messages.value.length > 0) {
      if (!pollingInterval) startPolling();
      return;
    }
    resetState()
    activeTeamId.value = teamId;
    messages.value = [];
    hasMoreHistory.value = true;
    isLoading.value = true;
    isLoadingHistory.value = false;

    try {
      console.log(`[Chat] Entering room ${teamId}`);
      const data = await getChatMessages(teamId);
      messages.value = data || [];
    } catch (error) {
      console.error('[Chat] Failed to load initial messages:', error);
      toast.error('无法加载聊天记录');
    } finally {
      isLoading.value = false;
      startPolling(); // 加载完成后开启轮询
    }
  };

  /**
   * 轮询：获取最新消息 (使用 after_msg_id)
   */
  const fetchNewMessages = async () => {
    if (!activeTeamId.value) return;

    try {
      const cursor = newestMsgId.value;
      const newMsgs = await getChatMessages(activeTeamId.value, {after_msg_id: cursor});
      if (newMsgs && newMsgs.length > 0) {
        mergeMessages(newMsgs);
        console.log(`[Chat] Synced ${newMsgs.length} new messages.`);
      }
    } catch (error) {
      console.warn('[Chat] Polling error:', error);
    }
  };

  /**
   * 加载更多历史消息 (使用 before_msg_id)
   * UI 组件可以在滚动到顶部时调用此方法
   */
  const loadHistoryMessages = async (): Promise<number> => {
    // 如果正在加载、没有团队ID、或者已知没有更多数据，则直接返回
    if (!activeTeamId.value || isLoadingHistory.value || !hasMoreHistory.value) return 0;

    const cursor = oldestMsgId.value;
    if (!cursor) return 0;

    isLoadingHistory.value = true;
    try {
      console.log(`[Chat] Loading history before ${cursor}...`);
      const historyMsgs = await getChatMessages(activeTeamId.value, {before_msg_id: cursor});

      if (historyMsgs && historyMsgs.length > 0) {
        const addedCount = mergeMessages(historyMsgs);
        console.log(`[Chat] History loaded. Added ${addedCount} new messages.`);
        return addedCount;
      } else {
        console.log('[Chat] No more history.');
        hasMoreHistory.value = false; // 标记没有更多了
        return 0;
      }
    } catch (error) {
      console.error('[Chat] Failed to load history:', error);
      return 0;
    } finally {
      isLoadingHistory.value = false;
    }
  };

  /**
   * 辅助函数：合并消息并去重
   */
  const mergeMessages = (incoming: TeamChat[]): number => {
    const existingIds = new Set(messages.value.map(m => m.id));
    const uniqueIncoming = incoming.filter(m => !existingIds.has(m.id));
    if (uniqueIncoming.length > 0) {
      messages.value = [...messages.value, ...uniqueIncoming];
    }
    return uniqueIncoming.length;
  };

  // --- 轮询控制 ---

  const startPolling = () => {
    stopPolling();
    // 立即执行一次检查，然后开始定时器
    // fetchNewMessages();
    // @ts-ignore
    pollingInterval = setInterval(fetchNewMessages, POLLING_RATE);
  };

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  };

  const clearChat = () => {
    stopPolling();
    activeTeamId.value = null;
    messages.value = [];
  };

  // --- 交互逻辑 ---

  const sendMessage = async (content: string, tag: string = 'text') => {
    if (!activeTeamId.value) {
      toast.error('未选择团队');
      return false;
    }
    if (!content.trim()) return false;

    isSending.value = true;
    try {
      const payload: NewTeamChatRequest = {content, tag};
      await sendChatMessage(activeTeamId.value, payload);

      // 发送成功后立即尝试拉取最新消息，提升体验
      await fetchNewMessages();
      return true;
    } catch (error) {
      console.error('[Chat] Send failed:', error);
      toast.error('发送失败');
      return false;
    } finally {
      isSending.value = false;
    }
  };

  const sendFile = async (file: File, tag: string = 'file') => {
    if (!activeTeamId.value) return false;

    isSending.value = true;
    const toastId = toast.loading('正在上传文件...');

    try {
      const payload: FileUploadRequest = {file, tag};
      await uploadChatFile(activeTeamId.value, payload);

      toast.success('文件上传成功', {id: toastId});
      await fetchNewMessages();
      return true;
    } catch (error) {
      console.error('[Chat] File upload failed:', error);
      toast.error('文件上传失败', {id: toastId});
      return false;
    } finally {
      isSending.value = false;
    }
  };

  const deleteMessage = async (msgId: string) => {
    if (!activeTeamId.value) return;
    try {
      await deleteChatMessage(activeTeamId.value, {id: msgId});
      // 乐观更新：直接在前端移除，不等轮询
      messages.value = messages.value.filter(m => m.id !== msgId);
      toast.success('消息已撤回');
    } catch (error) {
      console.error('Delete failed', error);
      toast.error('撤回失败');
    }
  };

  return {
    messages,
    sortedMessages,
    isLoading,
    isSending,
    activeTeamId,
    switchChatRoom,
    loadHistoryMessages,
    fetchNewMessages,
    isLoadingHistory,
    hasMoreHistory,
    clearChat,
    sendMessage,
    sendFile,
    deleteMessage
  };
});
