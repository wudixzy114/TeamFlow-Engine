<!-- src/views/weekly/WeeklyDigestView.vue -->
<template>
  <div class="h-full w-full flex flex-col overflow-hidden">

    <!-- 滚动区域 -->
    <div class="flex-1 overflow-y-auto p-6 md:p-8 scrollbar-hide">

      <!-- 1. Header Area -->
      <header class="w-full flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 animate-slide-in-fast">

        <!-- Title & Subtitle -->
        <div>
          <h1 class="text-h1 mb-1 flex items-center gap-3">
            <span class="i-carbon-notebook text-primary"></span>
            <span>Weekly Digest</span>
          </h1>
          <p class="text-muted text-sm">回顾团队表现，沉淀心流时刻。</p>
        </div>

        <!-- Week Navigator -->
        <div class="glass-panel p-1.5 flex items-center gap-1 shadow-lg">
          <button
            :disabled="isLoading"
            class="btn-icon w-8 h-8 rounded-lg hover:bg-surface text-muted hover:text-text disabled:opacity-30 transition-colors"
            title="上一周"
            @click="changeWeek(-1)"
          >
            <span class="i-carbon-chevron-left text-lg"></span>
          </button>

          <div
            class="px-4 py-1 text-center min-w-[160px] flex flex-col items-center justify-center border-x border-border/10">
            <span class="text-[10px] uppercase text-muted tracking-wider font-bold">Current Period</span>
            <div class="text-sm font-bold text-text font-mono flex items-center gap-2">
              <span v-if="digestData">{{ digestData.week_range.start }}</span>
              <span v-else class="opacity-50">Loading...</span>
            </div>
          </div>

          <button
            :disabled="isLoading"
            class="btn-icon w-8 h-8 rounded-lg hover:bg-surface text-muted hover:text-text disabled:opacity-30 transition-colors"
            title="下一周"
            @click="changeWeek(1)"
          >
            <span class="i-carbon-chevron-right text-lg"></span>
          </button>
        </div>
      </header>

      <!-- 2. Main Content -->
      <main class="w-full max-w-7xl mx-auto space-y-6 pb-12">

        <!-- Loading Skeleton -->
        <div v-if="isLoading && !digestData" class="grid grid-cols-1 md:grid-cols-4 gap-6 animate-pulse">
          <div v-for="i in 4" :key="i" class="h-32 bg-surface/30 rounded-2xl"></div>
          <div class="col-span-full h-96 bg-surface/30 rounded-2xl"></div>
        </div>

        <!-- Data Content -->
        <transition
          enter-active-class="transition duration-500 ease-out"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
          mode="out-in"
        >
          <div v-if="digestData && !isLoading" class="flex flex-col gap-6">

            <!-- KPI Cards (Bento Grid) -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

              <!-- 1. Deep Focus -->
              <div class="glass-panel p-6 relative overflow-hidden group">
                <div
                  class="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-all"></div>
                <div class="relative z-10">
                  <div class="flex items-center gap-2 text-primary mb-3">
                    <span class="i-carbon-timer text-xl"></span>
                    <span class="text-xs font-bold uppercase tracking-wider">Deep Focus</span>
                  </div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-3xl font-bold text-text font-mono tracking-tight">
                      {{ digestData.total_focus_hours.toFixed(1) }}
                    </span>
                    <span class="text-sm text-muted">hrs</span>
                  </div>
                </div>
              </div>

              <!-- 2. Appreciation -->
              <div class="glass-panel p-6 relative overflow-hidden group">
                <div
                  class="absolute -right-4 -top-4 w-24 h-24 bg-accent/10 rounded-full blur-2xl group-hover:bg-accent/20 transition-all"></div>
                <div class="relative z-10">
                  <div class="flex items-center gap-2 text-accent mb-3">
                    <span class="i-carbon-trophy text-xl"></span>
                    <span class="text-xs font-bold uppercase tracking-wider">Kudos Received</span>
                  </div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-3xl font-bold text-text font-mono tracking-tight">
                      {{ digestData.kudos_received }}
                    </span>
                    <span class="text-sm text-muted">cards</span>
                  </div>
                </div>
              </div>

              <!-- 3. Top Booster -->
              <div class="glass-panel p-6 relative overflow-hidden group border-l-2 border-l-emerald-500/50">
                <div
                  class="absolute -right-4 -top-4 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all"></div>
                <div class="relative z-10">
                  <div class="flex items-center gap-2 text-emerald-400 mb-3">
                    <span class="i-carbon-rocket text-xl"></span>
                    <span class="text-xs font-bold uppercase tracking-wider">Top Booster</span>
                  </div>
                  <div
                    :title="digestData.top_booster"
                    class="text-xl font-bold text-text truncate"
                  >
                    {{ digestData.top_booster || 'No Data' }}
                  </div>
                </div>
              </div>

              <!-- 4. Top Blocker -->
              <div class="glass-panel p-6 relative overflow-hidden group border-l-2 border-l-rose-500/50">
                <div
                  class="absolute -right-4 -top-4 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/20 transition-all"></div>
                <div class="relative z-10">
                  <div class="flex items-center gap-2 text-rose-400 mb-3">
                    <span class="i-carbon-road-barrier text-xl"></span>
                    <span class="text-xs font-bold uppercase tracking-wider">Top Blocker</span>
                  </div>
                  <div
                    :title="digestData.top_blocker"
                    class="text-xl font-bold text-text truncate"
                  >
                    {{ digestData.top_blocker || 'No Data' }}
                  </div>
                </div>
              </div>

            </div>

            <!-- Mindset Trend Chart -->
            <!-- 修复关键点：给父容器一个固定高度 (h-[500px])，防止 Flex 计算延迟导致 ECharts 获取高度为 0 -->
            <div class="glass-panel flex flex-col h-[500px]">
              <div class="px-6 py-4 border-b border-border/10 flex justify-between items-center flex-shrink-0">
                <div class="flex items-center gap-3">
                  <div class="p-2 rounded-lg bg-surface border border-border/10">
                    <span class="i-carbon-chart-radar text-lg text-primary"></span>
                  </div>
                  <div>
                    <h3 class="font-bold text-text text-sm">Flow State Trajectory</h3>
                    <p class="text-xs text-muted">团队心流状态与挑战/技能匹配度回顾</p>
                  </div>
                </div>
              </div>

              <!-- 修复关键点：内部容器明确 w-full h-full，且 position relative -->
              <div class="w-full h-full relative p-2 overflow-hidden">
                <FlowMoodChart :data="digestData.mindset_trend"/>
              </div>
            </div>

          </div>

          <!-- Empty State -->
          <div v-else-if="!isLoading"
               class="h-96 flex flex-col items-center justify-center glass-panel border border-dashed border-border/30">
            <div class="w-20 h-20 rounded-full bg-surface/50 flex items-center justify-center mb-4">
              <span class="i-carbon-search text-4xl text-muted/50"></span>
            </div>
            <h3 class="text-lg font-bold text-text">本周暂无数据</h3>
            <p class="text-muted text-sm mt-1">该时间段内没有检测到团队签到记录。</p>
            <button class="btn-primary mt-6" @click="changeWeek(0)">
              回到本周
            </button>
          </div>
        </transition>

      </main>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, computed, ref} from 'vue';
import {useWeeklyDigestStore} from '@/stores/weeklyDigest';
import FlowMoodChart from '@/components/dashboard/FlowMoodChart.vue';

const store = useWeeklyDigestStore();

// --- State ---
const currentDisplayDate = ref(new Date());

// --- Computed ---
const digestData = computed(() => store.digestData);
const isLoading = computed(() => store.isLoading);

// --- Actions ---

onMounted(() => {
  store.fetchDigestForDate(currentDisplayDate.value);
});

const changeWeek = async (offset: number) => {
  if (isLoading.value) return;

  if (offset === 0) {
    // Reset to today
    currentDisplayDate.value = new Date();
  } else {
    // Calculate new date
    const newDate = new Date(currentDisplayDate.value);
    newDate.setDate(newDate.getDate() + (offset * 7));
    currentDisplayDate.value = newDate;
  }

  await store.fetchDigestForDate(currentDisplayDate.value);
};
</script>

<style scoped>
.btn-icon {
  @apply flex items-center justify-center transition-all duration-200 active:scale-95;
}
</style>
