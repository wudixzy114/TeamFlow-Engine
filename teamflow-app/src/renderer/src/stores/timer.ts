// src/stores/timer.ts
import {defineStore} from 'pinia';
import {computed, ref, watch} from 'vue';
import {useFlowSessionStore} from '@/stores/flowSession'; // 引入之前的 session store 用于提交

// --- 类型定义 ---
export interface TimeBlock {
  id: string;
  type: 'focus' | 'shortBreak' | 'longBreak';
  duration: number; // 初始设定时长 (分钟)
  remainingTime: number; // 剩余秒数
  elapsed: number; // 已经花费的秒数
  status: 'pending' | 'completed';
  taskTitle?: string;
  startTime?: string; // ISO String，序列化友好
}

export type TimerMode = 'timeline' | 'free';

export const useTimerStore = defineStore('timer', () => {
  const flowSessionStore = useFlowSessionStore();

  // --- State (持久化数据) ---
  const timeline = ref<TimeBlock[]>([]);
  const activeBlockIndex = ref(-1);
  const mode = ref<TimerMode>('timeline');
  const settings = ref({
    focusTime: 25,
    shortBreakTime: 5,
    longBreakTime: 15,
    autoStartBreaks: false,
  });

  // --- State (运行时状态，非持久化或需特殊处理) ---
  const isRunning = ref(false);
  let timerInterval: number | null = null;

  // --- Getters ---
  const activeBlock = computed(() => {
    if (activeBlockIndex.value >= 0 && activeBlockIndex.value < timeline.value.length) {
      return timeline.value[activeBlockIndex.value];
    }
    return undefined;
  });

  // --- Actions ---

  // 1. 初始化：从 localStorage 读取数据
  function init() {
    const saved = localStorage.getItem('flow_timer_state');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        timeline.value = parsed.timeline || [];
        activeBlockIndex.value = parsed.activeBlockIndex ?? -1;
        mode.value = parsed.mode || 'timeline';
        settings.value = {...settings.value, ...parsed.settings};
      } catch (e) {
        console.error('Failed to load timer state', e);
      }
    }

    // 如果没有数据，初始化默认值
    if (timeline.value.length === 0) {
      addBlock('focus');
      addBlock('shortBreak');
      activeBlockIndex.value = 0;
    }
  }

  // 2. 核心：计时器逻辑 (移到 Store 中，这样切换路由计时器不会停)
  function toggleTimer() {
    if (!activeBlock.value) return;

    // 如果已完成，不操作
    if (activeBlock.value.status === 'completed') return;

    if (isRunning.value) {
      pauseTimer();
    } else {
      startTimer();
    }
  }

  function startTimer() {
    if (!activeBlock.value) return;

    isRunning.value = true;

    // 记录开始时间
    if (activeBlock.value.elapsed === 0 && !activeBlock.value.startTime) {
      activeBlock.value.startTime = new Date().toISOString();
    }

    // 清除旧的 interval 防止重叠
    if (timerInterval) clearInterval(timerInterval);

    timerInterval = window.setInterval(() => {
      if (!activeBlock.value) {
        pauseTimer();
        return;
      }

      if (activeBlock.value.remainingTime > 0) {
        activeBlock.value.remainingTime--;
        activeBlock.value.elapsed++;
      } else {
        completeTimer();
      }
    }, 1000);
  }

  function pauseTimer() {
    isRunning.value = false;
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  async function completeTimer() {
    pauseTimer();
    const block = activeBlock.value;
    if (!block) return;

    block.status = 'completed';

    // 提交数据
    const timeSpentMins = Math.ceil(block.elapsed / 60);
    const finalDuration = timeSpentMins > 0 ? timeSpentMins : 1;

    // 提交到后端
    await flowSessionStore.submitFlowSession({
      task_description: getBlockTitle(block),
      duration_minutes: finalDuration,
      start_time: block.startTime || new Date().toISOString()
    });
    await flowSessionStore.fetchSessionHistory();

    // 自动流转逻辑
    if (activeBlockIndex.value < timeline.value.length - 1) {
      activeBlockIndex.value++;
      if (settings.value.autoStartBreaks) {
        setTimeout(() => startTimer(), 1000);
      }
    }
  }

  // --- Helper Actions ---
  function addBlock(type: 'focus' | 'shortBreak' | 'longBreak') {
    const duration = type === 'focus' ? settings.value.focusTime
      : type === 'shortBreak' ? settings.value.shortBreakTime
        : settings.value.longBreakTime;

    timeline.value.push({
      id: Date.now().toString() + Math.random(),
      type,
      duration,
      remainingTime: duration * 60,
      elapsed: 0,
      status: 'pending',
      taskTitle: ''
    });

    if (activeBlockIndex.value === -1) activeBlockIndex.value = 0;
  }

  function removeBlock(index: number) {
    if (isRunning.value) return;

    timeline.value.splice(index, 1);

    // 修正 activeIndex
    if (index === activeBlockIndex.value) {
      if (timeline.value.length > index) {
        // 保持当前 index
      } else if (timeline.value.length > 0) {
        activeBlockIndex.value = timeline.value.length - 1;
      } else {
        activeBlockIndex.value = -1;
      }
    } else if (index < activeBlockIndex.value) {
      activeBlockIndex.value--;
    }
  }

  function repeatBlock(block: TimeBlock, index: number) {
    const newBlock: TimeBlock = {
      ...block,
      id: Date.now().toString() + Math.random(),
      status: 'pending',
      elapsed: 0,
      remainingTime: block.duration * 60,
      startTime: undefined
    };
    timeline.value.splice(index + 1, 0, newBlock);
    activeBlockIndex.value = index + 1;
  }

  function resetCurrentProgress() {
    pauseTimer();
    if (activeBlock.value && activeBlock.value.status !== 'completed') {
      activeBlock.value.remainingTime = activeBlock.value.duration * 60;
      activeBlock.value.elapsed = 0;
      activeBlock.value.startTime = undefined;
    }
  }

  function adjustTime(minutes: number) {
    if (activeBlock.value && activeBlock.value.status !== 'completed') {
      activeBlock.value.remainingTime += minutes * 60;
      if (activeBlock.value.remainingTime < 0) activeBlock.value.remainingTime = 0;
    }
  }

  // 辅助：获取标题
  function getBlockTitle(block?: TimeBlock) {
    if (!block) return 'Ready to Flow';
    if (block.type === 'focus') return block.taskTitle || 'Untitled Task';
    return block.type === 'shortBreak' ? 'Short Break' : 'Long Break';
  }

  // --- Persistence Watcher ---
  // 监听数据变化并保存到 LocalStorage
  watch(
    [timeline, activeBlockIndex, mode, settings],
    () => {
      localStorage.setItem('flow_timer_state', JSON.stringify({
        timeline: timeline.value,
        activeBlockIndex: activeBlockIndex.value,
        mode: mode.value,
        settings: settings.value,
      }));
    },
    {deep: true}
  );

  function addSessionBlock(payload: {
    type: 'focus' | 'short_break' | 'long_break',
    duration?: number,
    taskTitle?: string,
    startNow?: boolean
  }) {
    const {type, duration, taskTitle, startNow = true} = payload;

    // 如果需要立即开始，且当前正在运行，先暂停
    if (startNow && isRunning.value) {
      pauseTimer();
    }

    // 确定时长
    let finalDuration = duration;
    if (!finalDuration) {
      if (type === 'focus') finalDuration = settings.value.focusTime;
      else if (type === 'short_break') finalDuration = settings.value.shortBreakTime;
      else finalDuration = settings.value.longBreakTime;
    }

    // 映射类型
    const blockType = type === 'focus' ? 'focus' : (type === 'short_break' ? 'shortBreak' : 'longBreak');

    const newBlock: TimeBlock = {
      id: Date.now().toString() + Math.random(),
      type: blockType,
      duration: finalDuration,
      remainingTime: finalDuration * 60,
      elapsed: 0,
      status: 'pending',
      taskTitle: taskTitle || (type === 'focus' ? 'Deep Work' : '')
    };

    // 插入逻辑：如果是 startNow，插入到当前之后并跳转；否则加到末尾
    if (startNow) {
      // 如果当前列表为空
      if (timeline.value.length === 0) {
        timeline.value.push(newBlock);
        activeBlockIndex.value = 0;
      } else {
        // 插入到当前位置之后
        timeline.value.splice(activeBlockIndex.value + 1, 0, newBlock);
        activeBlockIndex.value += 1;
      }
      // 启动
      setTimeout(() => startTimer(), 100);
    } else {
      timeline.value.push(newBlock);
    }
  }

  /**
   * 修改当前活动 Block (支持重命名、调整时间)
   * 自动处理 暂停 -> 修改 -> 恢复 的逻辑
   */
  function modifyActiveBlock(payload: {
    newTitle?: string;
    timeAdjustment?: number; // 相对增减 (分钟)
    setDuration?: number;    // 绝对设置 (分钟)
  }) {
    if (!activeBlock.value || activeBlock.value.status === 'completed') return;

    const wasRunning = isRunning.value;
    if (wasRunning) {
      pauseTimer();
    }

    // 1. 修改标题
    if (payload.newTitle && activeBlock.value.type === 'focus') {
      activeBlock.value.taskTitle = payload.newTitle;
    }

    // 2. 修改时间
    if (payload.setDuration !== undefined && payload.setDuration > 0) {
      // 绝对设置
      activeBlock.value.remainingTime = Math.floor(payload.setDuration * 60);
      // 可选：更新原始 duration 以保持一致性，或者仅改变 remainingTime
      activeBlock.value.duration = payload.setDuration;
    } else if (payload.timeAdjustment !== undefined) {
      // 相对设置
      let newTime = activeBlock.value.remainingTime + (payload.timeAdjustment * 60);
      if (newTime < 0) newTime = 0;
      activeBlock.value.remainingTime = newTime;
    }

    // 如果之前是运行的，且时间没归零，则恢复
    if (wasRunning && activeBlock.value.remainingTime > 0) {
      startTimer();
    }
  }

  function skipCurrentBlock() {
    // 1. 先暂停当前任务
    if (isRunning.value) {
      pauseTimer();
    }

    // 2. 检查是否有下一个任务
    if (activeBlockIndex.value < timeline.value.length - 1) {
      // 移动索引
      activeBlockIndex.value++;

      // 3. 立即启动下一个任务（保持心流连续性）
      // 使用 setTimeout 确保 Vue 响应式状态更新完毕
      setTimeout(() => {
        startTimer();
      }, 100);
    } else {
      // 如果已经是最后一个，保持暂停状态，或者可以重置当前任务
      console.log('No next block to skip to.');
      // 可选：通知用户已是最后任务
    }
  }


  return {
    // State
    timeline,
    activeBlockIndex,
    mode,
    settings,
    isRunning,
    activeBlock,
    // Actions
    init,
    toggleTimer,
    startTimer,
    pauseTimer,
    addBlock,
    removeBlock,
    repeatBlock,
    resetCurrentProgress,
    adjustTime,
    getBlockTitle,

    addSessionBlock,
    modifyActiveBlock,
    skipCurrentBlock
  };
});
