import {onMounted, onUnmounted} from 'vue';
import {useTimerStore} from '@/stores/timer';
import {useThemeStore} from '@/stores/theme'; // 新增
import {useHighlightsStore} from '@/stores/highlights'; // 新增
import {useCheckinStore} from '@/stores/checkin'; // 新增

export function useAiController() {
  const timerStore = useTimerStore();
  const themeStore = useThemeStore();
  const highlightsStore = useHighlightsStore();
  const checkinStore = useCheckinStore();

  let stopActionListener: (() => void) | undefined;

  const handleAction = (payload: { action: string, args: any }) => {
    console.log('[AI Controller] Received action:', payload);
    const {action, args} = payload;

    switch (action) {
      // 1. 添加任务/休息
      case 'timer:manage-session':
        timerStore.addSessionBlock({
          type: args.type, // 'focus', 'short_break', 'long_break'
          duration: args.duration,
          taskTitle: args.task_description,
          startNow: args.start_immediately !== false // 默认为 true
        });
        break;

      // 2. 控制 (暂停/继续)
      case 'timer:control':
        if (args.command === 'pause') {
          timerStore.pauseTimer();
        } else if (args.command === 'resume') {
          timerStore.startTimer();
        }
        break;

      // 3. 修改当前任务
      case 'timer:modify-active':
        timerStore.modifyActiveBlock({
          newTitle: args.new_description,
          timeAdjustment: args.time_adjustment,
          setDuration: args.set_duration
        });
        break;
      case 'timer:skip':
        timerStore.skipCurrentBlock();
        break;

      case 'ui:set-theme':
        if (args.theme) {
          themeStore.setTheme(args.theme);
        }
        break;
      case 'ui:cycle-theme':
        themeStore.nextTheme();
        break;

      case 'social:post-highlight':
        if (args.content) {
          highlightsStore.addHighlight(args.content);
          console.log('AI posted highlight:', args.content);
        }
        break;

      // --- Checkin Actions ---
      case 'flow:submit-checkin':
        checkinStore.submitCheckin({
          challenge_level: args.challenge_level,
          skill_level: args.skill_level,
          achievement_text: args.achievement_text || null,
          obstacle_text: args.obstacle_text || null
        });
        break;

      default:
        console.warn('Unknown AI action:', action);
    }
  };

  // 注册监听
  onMounted(() => {
    if (window && window.ai) {
      if (stopActionListener) stopActionListener();
      window.ai.onRendererAction(handleAction);
    }
  });

  onUnmounted(() => {
    if (stopActionListener) {
      stopActionListener();
      stopActionListener = undefined;
      console.log('[AI Controller] Listener removed');
    }
  });
}
