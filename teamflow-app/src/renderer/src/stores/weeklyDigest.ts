import {defineStore} from 'pinia';
import {ref} from 'vue';
import {api} from '@/api';
import {toast} from 'vue-sonner'; // 替换 ElMessage

// 帮助函数：格式化日期为 'YYYY-MM-DD'
function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export const useWeeklyDigestStore = defineStore('weeklyDigest', () => {
  // --- State ---
  const digestData = ref<WeeklyDigestData | null>(null);
  const selectedDate = ref<Date>(new Date()); // 默认选择今天
  const isLoading = ref(false);

  // --- Actions ---

  /**
   * 设置查询日期并获取周报数据
   * @param date - 新选择的日期
   */
  async function fetchDigestForDate(date: Date) {
    selectedDate.value = date;
    const dateString = formatDate(date);

    isLoading.value = true;
    try {
      // 使用 api.me 调用 getMyWeeklyDigest
      digestData.value = await api.me.getMyWeeklyDigest(dateString);
    } catch (error) {
      console.error('Failed to fetch weekly digest:', error);
      digestData.value = null; // 加载失败时清空数据
      toast.error('获取周报数据失败');
    } finally {
      isLoading.value = false;
    }
  }

  return {
    digestData,
    selectedDate,
    isLoading,
    fetchDigestForDate,
  };
});
