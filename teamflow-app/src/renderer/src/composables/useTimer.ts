import {ref, computed, onUnmounted} from 'vue';

type TimerId = ReturnType<typeof setInterval>;

export function useTimer(initialSeconds: number) {
  const duration = ref(initialSeconds);
  const timeLeft = ref(initialSeconds);
  const isRunning = ref(false);
  const isFinished = ref(false);

  let timerId: TimerId | null = null;
  let endTime: number | null = null;

  const update = () => {
    if (endTime) {
      const remaining = Math.round((endTime - Date.now()) / 1000);
      if (remaining <= 0) {
        timeLeft.value = 0;
        isRunning.value = false;
        isFinished.value = true;
        if (timerId) clearInterval(timerId);
      } else {
        timeLeft.value = remaining;
      }
    }
  };

  const start = (seconds?: number) => {
    if (isRunning.value) return;
    if (seconds) {
      duration.value = seconds;
      timeLeft.value = seconds;
    }
    endTime = Date.now() + timeLeft.value * 1000;
    isRunning.value = true;
    isFinished.value = false;
    if (timerId) clearInterval(timerId);
    timerId = setInterval(update, 1000);
  };

  const pause = () => {
    isRunning.value = false;
    if (timerId) clearInterval(timerId);
  };

  const reset = (seconds?: number) => {
    pause();
    duration.value = seconds ?? duration.value;
    timeLeft.value = duration.value;
    isFinished.value = false;
  };

  onUnmounted(() => {
    if (timerId) clearInterval(timerId);
  });

  const formattedTime = computed(() => {
    const minutes = Math.floor(timeLeft.value / 60).toString().padStart(2, '0');
    const seconds = (timeLeft.value % 60).toString().padStart(2, '0');
    return `${minutes}:${seconds}`;
  });

  const progress = computed(() => {
    if (duration.value === 0) return 0;
    const currentLeft = Math.max(0, timeLeft.value);
    return ((duration.value - currentLeft) / duration.value) * 100;
  });

  return {
    timeLeft,
    isRunning,
    isFinished,
    formattedTime,
    progress,
    start,
    pause,
    reset,
  };
}
