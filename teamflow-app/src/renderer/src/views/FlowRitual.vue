<template>
  <!-- 外层容器 -->
  <div
    class="w-full h-full flex flex-col lg:flex-row p-4 lg:p-6 gap-4 lg:gap-6 overflow-hidden bg-bg-dark text-text-main relative select-none">

    <!-- 全局通知 Toast -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform -translate-y-5 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-5 opacity-0"
    >
      <div v-if="notification.show"
           class="absolute top-6 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl glass-panel border-primary/30 shadow-glow-primary flex items-center gap-3 backdrop-blur-xl pointer-events-none">
        <div class="i-ph-info-fill text-primary text-xl"></div>
        <span class="text-sm font-medium">{{ notification.message }}</span>
      </div>
    </Transition>

    <!-- 背景氛围 -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div
        class="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] animate-pulse-slow"></div>
      <div
        class="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[120px] animate-pulse-slow delay-2000"></div>
    </div>

    <!-- 左侧：HUD 仪表盘 -->
    <div
      class="w-full lg:w-[420px] xl:w-[480px] shrink-0 h-full flex flex-col items-center justify-center relative glass-panel border border-white/5 shadow-2xl transition-all duration-300">

      <!-- 顶部状态栏 -->
      <div class="absolute top-6 w-full px-8 flex justify-between items-center z-20">
        <!-- 系统状态 -->
        <div class="flex items-center gap-2 text-xs font-mono text-text-muted tracking-widest uppercase">
          <div :class="isSystemReady ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-amber-500 animate-pulse'"
               class="w-2 h-2 rounded-full transition-colors duration-300"></div>
          {{ isSystemReady ? 'ONLINE' : 'RECOVERING...' }}
        </div>

        <!-- 模式切换开关 -->
        <div :class="{'opacity-50 pointer-events-none': timerStore.isRunning}"
             class="flex bg-black/40 rounded-lg p-1 border border-white/10">
          <button
            :class="timerStore.mode === 'timeline' ? 'bg-white/10 text-white shadow-sm' : 'text-text-muted hover:text-white'"
            class="px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all flex items-center gap-1"
            @click="switchMode('timeline')">
            <div class="i-ph-list-dashes-bold"></div>
            Timeline
          </button>
          <button
            :class="timerStore.mode === 'free' ? 'bg-primary/20 text-primary shadow-glow-primary/20' : 'text-text-muted hover:text-white'"
            class="px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all flex items-center gap-1"
            @click="switchMode('free')">
            <div class="i-ph-infinity-bold"></div>
            Focus
          </button>
        </div>

        <button class="text-text-muted hover:text-white transition-colors p-2 rounded-full hover:bg-white/5"
                @click="isSettingsOpen = true">
          <div class="i-ph-gear-six-fill text-xl"></div>
        </button>
      </div>

      <!-- 核心计时器 -->
      <div class="relative z-10 flex flex-col items-center justify-center h-full w-full">
        <!-- 阶段胶囊 -->
        <div
          class="mb-10 flex items-center gap-3 px-6 py-2 rounded-full bg-black/40 border border-white/10 backdrop-blur-md shadow-lg z-30">
           <span :class="currentBlockColorClass"
                 class="text-xs font-bold tracking-[0.2em] uppercase transition-colors duration-500">
            {{ currentBlockLabel }}
          </span>
        </div>

        <!-- 进度环 -->
        <div class="relative w-[320px] h-[320px] xl:w-[360px] xl:h-[360px] group cursor-pointer select-none"
             @click="handleToggleTimer">
          <!-- 装饰环 -->
          <div class="absolute inset-0 rounded-full border border-white/5 scale-105 z-0"></div>
          <div
            class="absolute inset-0 rounded-full border border-white/10 scale-110 border-dashed opacity-30 animate-[spin_120s_linear_infinite] z-0"></div>

          <!-- SVG (层级 z-10) -->
          <svg
            class="absolute inset-0 w-full h-full transform -rotate-90 drop-shadow-[0_0_20px_rgba(0,0,0,0.5)] z-10 pointer-events-none">
            <circle class="stroke-white/5 fill-none" cx="50%" cy="50%" r="150" stroke-width="4"/>
            <circle
              :class="currentBlockStrokeClass"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="strokeOffset"
              class="fill-none transition-all duration-1000 ease-linear shadow-[0_0_30px_currentColor]"
              cx="50%"
              cy="50%" r="150" stroke-linecap="round" stroke-width="8"
            />
          </svg>

          <!-- 中央信息 -->
          <div class="absolute inset-0 flex flex-col items-center justify-center z-20 pointer-events-none">
            <!-- 时间 -->
            <div
              class="text-[4.5rem] xl:text-[5rem] leading-none font-mono font-bold tracking-tighter tabular-nums text-white text-shadow-glow mb-4">
              {{ formattedTime }}
            </div>

            <!-- 当前任务描述 -->
            <div class="flex flex-col items-center w-[70%] px-4 pointer-events-auto">
              <span v-if="timerStore.activeBlock?.type === 'focus'"
                    class="text-[10px] text-primary font-mono mb-2 uppercase tracking-widest border border-primary/30 px-1.5 py-0.5 rounded bg-black/50 backdrop-blur-sm">
                Current Task
              </span>
              <p
                class="text-sm xl:text-base font-medium text-center line-clamp-2 w-full text-gray-200 leading-tight min-h-[1.5em]">
                {{ timerStore.getBlockTitle(timerStore.activeBlock) }}
              </p>
              <!-- 显示已花费时间 -->
              <div v-if="(timerStore.activeBlock?.elapsed ?? 0) > 0"
                   class="mt-2 text-[10px] font-mono text-text-muted bg-black/30 px-2 py-0.5 rounded">
                <!-- 使用 (?.elapsed ?? 0) 确保即使是 undefined 也会被视为 0 -->
                Spent: {{ Math.floor((timerStore.activeBlock?.elapsed ?? 0) / 60) }}m
              </div>
            </div>

            <!-- 控制提示 Play/Pause -->
            <div
              class="absolute bottom-12 transition-all duration-300 transform translate-y-4 opacity-0 group-hover:opacity-100 group-hover:translate-y-0">
              <div
                :class="timerStore.isRunning ? 'i-ph-pause-circle-fill text-5xl text-amber-400' : 'i-ph-play-circle-fill text-5xl text-primary'"></div>
            </div>
          </div>
        </div>

        <!-- 快速控制栏 -->
        <div class="mt-10 h-10 flex items-center justify-center w-full relative z-30">
          <Transition
            enter-active-class="transition duration-300 ease-out"
            enter-from-class="opacity-0 translate-y-2"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-200 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 translate-y-2"
          >
            <!-- 运行中：空 -->
            <div v-if="timerStore.isRunning"></div>

            <!-- 暂停且未完成：允许 Reset 当前进度 -->
            <div v-else-if="timerStore.activeBlock && timerStore.activeBlock.status !== 'completed'" class="flex gap-4">
              <button v-if="timerStore.mode === 'free'"
                      class="btn-ghost text-xs font-mono border border-white/10 hover:bg-white/5 px-3 py-1.5 hover:text-primary transition-colors"
                      @click.stop="timerStore.adjustTime(-5)">-5m
              </button>
              <button
                class="btn-ghost text-xs font-mono border border-white/10 hover:bg-white/5 px-4 py-1.5 text-text-muted hover:text-white"
                @click.stop="timerStore.resetCurrentProgress">
                RESET PROGRESS
              </button>
              <button v-if="timerStore.mode === 'free'"
                      class="btn-ghost text-xs font-mono border border-white/10 hover:bg-white/5 px-3 py-1.5 hover:text-primary transition-colors"
                      @click.stop="timerStore.adjustTime(5)">+5m
              </button>
            </div>

            <!-- 已完成：显示 Again (新建一个) -->
            <div v-else-if="timerStore.activeBlock && timerStore.activeBlock.status === 'completed'" class="flex gap-4">
              <button
                class="btn-primary text-xs font-bold px-6 py-2 shadow-glow-primary"
                @click.stop="handleRepeatBlock(timerStore.activeBlock, timerStore.activeBlockIndex)">
                <div class="i-ph-arrows-clockwise-bold text-lg"></div>
                AGAIN
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- 右侧：控制中心 -->
    <div
      class="flex-1 h-full min-w-0 flex flex-col glass-panel overflow-hidden border-l border-white/5 shadow-2xl">

      <TabGroup :selectedIndex="selectedTabIndex" as="div" class="flex flex-col h-full w-full" @change="onTabChange">
        <!-- 头部 Tabs -->
        <div class="p-4 pb-2 bg-black/20 border-b border-white/5 z-10 shrink-0">
          <TabList class="flex space-x-1 rounded-xl bg-white/5 p-1">
            <Tab v-slot="{ selected }" as="template">
              <button
                :class="selected ? 'bg-primary/20 text-primary shadow-glow-primary/30' : 'text-text-muted hover:bg-white/[0.12] hover:text-white'"
                class="w-full rounded-lg py-2.5 text-sm font-medium leading-5 transition-all duration-300 outline-none flex items-center justify-center gap-2"
              >
                <div :class="timerStore.mode === 'free' ? 'i-ph-target-bold' : 'i-ph-kanban-bold'"></div>
                {{ timerStore.mode === 'free' ? 'Current Task' : 'Timeline' }}
              </button>
            </Tab>
            <Tab v-slot="{ selected }" as="template">
              <button
                :class="selected ? 'bg-primary/20 text-primary shadow-glow-primary/30' : 'text-text-muted hover:bg-white/[0.12] hover:text-white'"
                class="w-full rounded-lg py-2.5 text-sm font-medium leading-5 transition-all duration-300 outline-none flex items-center justify-center gap-2"
              >
                <div class="i-ph-clock-counter-clockwise-bold"></div>
                History
              </button>
            </Tab>
          </TabList>
        </div>

        <TabPanels class="flex-1 min-h-0 relative w-full">

          <!-- 面板 1: Timeline / Task Detail -->
          <TabPanel class="h-full flex flex-col outline-none">

            <!-- 模式 A: Timeline 列表模式 -->
            <div v-if="timerStore.mode === 'timeline'" class="h-full flex flex-col">
              <!-- 工具栏 -->
              <div class="p-4 border-b border-white/5 bg-white/[0.02] shrink-0">
                <div class="flex gap-2 mb-2">
                  <button
                    :disabled="timerStore.isRunning"
                    class="flex-1 py-2.5 rounded-lg border border-primary/30 bg-primary/5 text-primary text-xs font-bold hover:bg-primary/10 active:scale-95 transition-all flex-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="timerStore.addBlock('focus')">
                    <div class="i-ph-brain text-sm"></div>
                    Focus
                  </button>
                  <button
                    :disabled="timerStore.isRunning"
                    class="flex-1 py-2.5 rounded-lg border border-green-500/30 bg-green-500/5 text-green-400 text-xs font-bold hover:bg-green-500/10 active:scale-95 transition-all flex-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="timerStore.addBlock('shortBreak')">
                    <div class="i-ph-coffee text-sm"></div>
                    Short
                  </button>
                  <button
                    :disabled="timerStore.isRunning"
                    class="flex-1 py-2.5 rounded-lg border border-purple-500/30 bg-purple-500/5 text-purple-400 text-xs font-bold hover:bg-purple-500/10 active:scale-95 transition-all flex-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="timerStore.addBlock('longBreak')">
                    <div class="i-ph-armchair text-sm"></div>
                    Long
                  </button>
                </div>
                <div class="text-[11px] text-text-muted text-center flex justify-between px-2 pt-1 font-mono">
                  <span v-if="timerStore.isRunning" class="text-amber-400 animate-pulse"><div
                    class="i-ph-lock-key inline-block align-middle mr-1"/>LOCKED</span>
                  <span v-else>EDIT MODE</span>
                  <span>FINISH: {{ estimatedFinishTime }}</span>
                </div>
              </div>

              <!-- 可拖拽列表 -->
              <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2 min-h-0">
                <div
                  v-for="(block, index) in timerStore.timeline"
                  :key="block.id"
                  :class="[
                    timerStore.activeBlockIndex === index ? 'bg-white/10 border-white/20' : 'bg-white/5 border-transparent',
                    block.status === 'completed' ? 'opacity-60 border-white/5 hover:border-white/5' : 'hover:border-white/10',
                    block.type === 'focus' ? 'border-l-4 border-l-primary' : block.type === 'shortBreak' ? 'border-l-4 border-l-green-500' : 'border-l-4 border-l-purple-500',
                    (timerStore.isRunning || block.status === 'completed') ? 'cursor-default' : 'cursor-grab active:cursor-grabbing'
                  ]"
                  :draggable="!timerStore.isRunning && block.status !== 'completed'"
                  class="relative flex items-center p-3 rounded-xl border transition-all duration-300 group overflow-hidden"
                  @click="onBlockClick(index)"
                  @dragstart="onDragStart($event, index)"
                  @drop="onDrop($event, index)"
                  @dragover.prevent
                >
                  <!-- 进度指示条 (背景) -->
                  <div v-if="timerStore.activeBlockIndex === index"
                       :style="{ width: (block.elapsed / (block.elapsed + block.remainingTime || 1)) * 100 + '%' }"
                       class="absolute left-0 top-0 bottom-0 bg-white/5 transition-all duration-1000 ease-linear z-0 pointer-events-none"></div>

                  <!-- 完成任务悬停层 -->
                  <div v-if="block.status === 'completed'"
                       class="absolute inset-0 bg-black/60 z-30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity backdrop-blur-[2px]">

                    <!-- Repeat 按钮 (保持居中) -->
                    <button class="btn-primary text-xs py-1.5 px-3 shadow-xl flex items-center gap-1.5"
                            @click.stop="handleRepeatBlock(block, index)">
                      <div class="i-ph-plus-bold"></div>
                      Repeat
                    </button>

                    <!-- 删除按钮 (移动到最右侧，使用 absolute 定位) -->
                    <button
                      class="absolute right-3 p-2 rounded-lg text-text-muted hover:bg-red-500/20 hover:text-red-400 transition-all"
                      title="Remove from timeline"
                      @click.stop="timerStore.removeBlock(index)">
                      <div class="i-ph-trash-simple-bold text-lg"></div>
                    </button>

                  </div>

                  <!-- 完成标记 -->
                  <div v-if="block.status === 'completed'" class="absolute right-3 top-3 text-green-500 z-20">
                    <div class="i-ph-check-circle-fill text-xl"></div>
                  </div>

                  <div :class="block.status === 'completed' ? 'pr-8' : ''" class="flex-1 min-w-0 relative z-10">
                    <div class="flex items-center justify-between mb-1">
                      <span
                        :class="block.type === 'focus' ? 'text-primary' : block.type === 'shortBreak' ? 'text-green-400' : 'text-purple-400'"
                        class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <div
                          :class="block.type === 'focus' ? 'i-ph-brain-fill' : block.type === 'shortBreak' ? 'i-ph-coffee-fill' : 'i-ph-armchair-fill'"></div>
                        {{
                          block.type === 'focus' ? 'Focus' : block.type === 'shortBreak' ? 'Short Break' : 'Long Break'
                        }}
                      </span>

                      <!-- 显示时间 -->
                      <span class="text-[10px] font-mono text-text-muted/80 bg-black/20 px-1.5 py-0.5 rounded">
                         <span v-if="block.status === 'completed'"
                               class="text-green-400 font-bold">Total: {{ Math.ceil(block.elapsed / 60) }}m</span>
                         <span v-else-if="timerStore.activeBlockIndex === index"
                               class="text-white font-bold">{{ formattedTimeBlock(block.remainingTime) }}</span>
                         <span v-else>{{ block.duration }}m</span>
                      </span>
                    </div>

                    <div class="flex items-center gap-2">
                      <div v-if="block.status !== 'completed'" class="i-ph-clock text-text-muted text-xs"></div>

                      <div v-if="block.status !== 'completed'">
                        <input
                          v-model.number="block.duration"
                          :disabled="timerStore.isRunning"
                          class="bg-transparent border-b border-dashed border-white/10 w-10 text-sm font-mono text-white text-center outline-none focus:border-primary transition-colors disabled:opacity-50 disabled:border-transparent"
                          type="number"
                          @change="onDurationChange(block)"
                          @click.stop
                        >
                        <span class="text-xs text-text-muted">min</span>
                      </div>

                      <div v-if="block.status !== 'completed'" class="h-4 w-[1px] bg-white/10 mx-1"></div>

                      <input
                        v-if="block.type === 'focus'"
                        v-model="block.taskTitle"
                        :disabled="block.status === 'completed'"
                        class="bg-transparent text-sm text-text-main placeholder-text-muted/30 focus:text-white outline-none flex-1 min-w-0 truncate border-b border-dashed border-transparent focus:border-white/20 hover:bg-white/5 px-1 rounded-t transition-colors disabled:hover:bg-transparent disabled:border-none disabled:text-text-muted"
                        placeholder="What are you working on?"
                        @click.stop
                      >
                      <span v-else
                            :class="block.status === 'completed' ? 'text-text-muted' : (block.type === 'shortBreak' ? 'text-green-400/70' : 'text-purple-400/70')"
                            class="text-sm font-medium italic flex-1 ml-2">
                        {{ block.type === 'shortBreak' ? 'Recharge Session' : 'Deep Rest' }}
                      </span>
                    </div>
                  </div>

                  <button
                    v-if="!timerStore.isRunning && block.status !== 'completed'"
                    class="ml-3 p-2 text-text-muted hover:text-red-400 hover:bg-white/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 z-20"
                    @click.stop="timerStore.removeBlock(index)">
                    <div class="i-ph-trash-simple-bold text-lg"></div>
                  </button>
                </div>

                <div v-if="timerStore.timeline.length === 0"
                     class="h-full flex flex-col items-center justify-center text-text-muted/40 border-2 border-dashed border-white/5 rounded-xl min-h-[200px]">
                  <p class="text-sm font-medium">Timeline Empty</p>
                </div>
                <div class="h-4"></div>
              </div>
            </div>

            <!-- 模式 B: Free Mode 专注任务详情 -->
            <div v-else class="h-full flex flex-col p-6 items-center justify-center relative">
              <div class="absolute inset-0 bg-primary/5 blur-3xl pointer-events-none"></div>

              <div v-if="timerStore.activeBlock" class="w-full max-w-sm relative z-10 text-center">
                <div class="i-ph-infinity text-6xl text-primary/30 mx-auto mb-6 animate-pulse-slow"></div>

                <h3 class="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-4">Current Session</h3>

                <div class="space-y-6">
                  <div v-if="timerStore.activeBlock.type === 'focus'">
                    <label class="block text-xs text-text-muted mb-2 uppercase">Task Title</label>
                    <input
                      v-model="timerStore.activeBlock.taskTitle"
                      :disabled="timerStore.activeBlock.status === 'completed'"
                      class="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-lg text-center text-white focus:border-primary/50 focus:shadow-glow-primary outline-none transition-all placeholder:text-text-muted/20 disabled:opacity-50"
                      placeholder="Enter your task..."
                    />
                  </div>
                  <div v-else>
                    <div class="text-xl font-bold text-white mb-2">{{
                        timerStore.getBlockTitle(timerStore.activeBlock)
                      }}
                    </div>
                    <div class="text-sm text-text-muted">Break Time</div>
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div
                      class="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col items-center group hover:bg-white/10 transition-colors">
                      <span class="text-xs text-text-muted mb-1 group-hover:text-primary transition-colors">Remaining (min)</span>
                      <input
                        v-if="timerStore.activeBlock.status !== 'completed'"
                        v-model.lazy="currentBlockDurationInput"
                        class="text-xl font-mono font-bold text-white bg-transparent text-center w-full outline-none border-b border-dashed border-transparent focus:border-primary/50 hover:border-white/20"
                        type="number"
                      />
                      <span v-else class="text-xl font-mono font-bold text-text-muted">0</span>
                    </div>

                    <div class="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col items-center">
                      <span class="text-xs text-text-muted mb-1">Total Spent</span>
                      <span class="text-xl font-mono font-bold text-white">{{
                          Math.floor((timerStore.activeBlock?.elapsed ?? 0) / 60)
                        }}m</span>
                    </div>
                  </div>

                  <div class="text-xs text-text-muted/50 mt-6">
                    Focus Mode active.
                  </div>
                </div>
              </div>

              <div v-else class="text-center text-text-muted">
                <p>No active block selected.</p>
                <button class="mt-4 btn-primary" @click="timerStore.addBlock('focus')">Start a Session</button>
              </div>
            </div>

          </TabPanel>

          <!-- 面板 2: 历史记录 (时间轴样式) -->
          <TabPanel class="h-full flex flex-col outline-none">
            <div class="p-4 shrink-0 flex justify-between items-center border-b border-white/5 bg-white/[0.02]">
              <span class="text-xs font-bold text-text-muted uppercase tracking-wider">Session Log</span>
              <button
                class="text-xs text-primary hover:text-white flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-white/5 transition-all"
                @click="flowSessionStore.fetchSessionHistory">
                <div :class="{'animate-spin': flowSessionStore.isLoading}" class="i-ph-arrows-clockwise"></div>
                Refresh
              </button>
            </div>

            <div class="flex-1 overflow-y-auto custom-scrollbar p-4 min-h-0">
              <div v-if="flowSessionStore.sessionHistory?.length"
                   class="relative ml-2 pl-6 border-l border-white/10 space-y-8 py-2">
                <div v-for="session in flowSessionStore.sessionHistory" :key="session.id" class="relative">
                  <div
                    class="absolute -left-[29px] top-1 w-3 h-3 rounded-full bg-bg-dark border-2 border-primary shadow-[0_0_10px_rgba(6,182,212,0.5)] z-10"></div>

                  <div class="flex flex-col">
                    <span class="text-xs font-mono text-text-muted mb-1">{{
                        new Date(session.start_time).toLocaleString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      }}</span>
                    <div class="p-3 bg-white/5 rounded-lg border border-white/5 hover:bg-white/10 transition-colors">
                      <div class="font-medium text-sm text-white mb-1">{{ session.task_description }}</div>
                      <div class="flex items-center gap-2">
                        <span class="text-[10px] font-bold bg-primary/20 text-primary px-1.5 py-0.5 rounded">{{
                            session.duration_minutes
                          }} min</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center py-20 text-text-muted/40">
                <div class="i-ph-clock-counter-clockwise text-4xl mb-2"></div>
                <span>No history yet</span>
              </div>
            </div>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>

    <!-- 设置弹窗 -->
    <TransitionRoot :show="isSettingsOpen" appear as="template">
      <Dialog as="div" class="relative z-50" @close="isSettingsOpen = false">
        <TransitionChild
          as="template" enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100"
          leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/80 backdrop-blur-md"/>
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              as="template" enter="duration-300 ease-out" enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="duration-200 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95"
            >
              <DialogPanel
                class="w-full max-w-lg transform overflow-hidden rounded-2xl bg-[#111827] border border-white/10 p-8 shadow-2xl transition-all">
                <DialogTitle class="text-xl font-bold text-white mb-2 flex items-center gap-3">
                  <div class="i-ph-faders-fill text-primary"></div>
                  Configuration
                </DialogTitle>
                <div class="space-y-6">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <span class="text-sm text-white flex items-center gap-2">Focus Session</span>
                      <div class="flex items-center gap-2">
                        <input v-model.number="timerStore.settings.focusTime"
                               class="bg-black/30 border border-primary/30 rounded-lg px-2 py-1 text-center text-primary font-mono focus:outline-none focus:border-primary w-20"
                               type="number">
                        <span class="text-xs text-text-muted">min</span>
                      </div>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-sm text-white flex items-center gap-2">Short Break</span>
                      <div class="flex items-center gap-2">
                        <input v-model.number="timerStore.settings.shortBreakTime"
                               class="bg-black/30 border border-green-500/30 rounded-lg px-2 py-1 text-center text-green-400 font-mono focus:outline-none focus:border-green-500 w-20"
                               type="number">
                        <span class="text-xs text-text-muted">min</span>
                      </div>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-sm text-white flex items-center gap-2">Long Break</span>
                      <div class="flex items-center gap-2">
                        <input v-model.number="timerStore.settings.longBreakTime"
                               class="bg-black/30 border border-purple-500/30 rounded-lg px-2 py-1 text-center text-purple-400 font-mono focus:outline-none focus:border-purple-500 w-20"
                               type="number">
                        <span class="text-xs text-text-muted">min</span>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center justify-between p-4 rounded-lg bg-white/5">
                    <div>
                      <div class="text-sm text-white">Auto-Advance Timeline</div>
                      <div class="text-xs text-text-muted mt-0.5">Start next block automatically</div>
                    </div>
                    <Switch v-model="timerStore.settings.autoStartBreaks"
                            :class="timerStore.settings.autoStartBreaks ? 'bg-primary' : 'bg-white/10'"
                            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none">
                      <span :class="timerStore.settings.autoStartBreaks ? 'translate-x-5' : 'translate-x-0'"
                            class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out"/>
                    </Switch>
                  </div>
                </div>
                <div class="mt-8 pt-6 border-t border-white/10 flex justify-end">
                  <button class="btn-primary" @click="isSettingsOpen = false">Save & Close</button>
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
import {ref, computed, onMounted} from 'vue';
import {useTimerStore, type TimeBlock, type TimerMode} from '@/stores/timer';
import {useFlowSessionStore} from '@/stores/flowSession';
import {
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogPanel,
  DialogTitle,
  Switch
} from '@headlessui/vue';

// --- 全局 Store ---
const timerStore = useTimerStore();
const flowSessionStore = useFlowSessionStore();

// --- 局部 UI 状态 ---
const isSystemReady = ref(false);
const isSettingsOpen = ref(false);
const selectedTabIndex = ref(0);
const notification = ref({show: false, message: ''});
let notificationTimeout: any = null;

const showNotify = (msg: string, duration: number = 3000) => {
  if (notificationTimeout) clearTimeout(notificationTimeout);
  notification.value = {show: true, message: msg};
  notificationTimeout = setTimeout(() => {
    notification.value.show = false;
  }, duration);
};

// --- UI Wrapper Functions ---
const switchMode = (newMode: TimerMode) => {
  if (timerStore.isRunning) {
    showNotify("Pause timer to switch modes.", 2000);
    return;
  }
  timerStore.mode = newMode;
  if (newMode === 'free' && !timerStore.activeBlock) {
    timerStore.addBlock('focus');
  }
  showNotify(`Switched to ${newMode === 'free' ? 'Focus View' : 'Timeline'} Mode`);
};

const handleToggleTimer = () => {
  if (!timerStore.activeBlock) {
    if (timerStore.timeline.length === 0) {
      timerStore.addBlock('focus');
    }
  }
  // Completed status handling is now inside store logic, UI just calls toggle
  if (timerStore.activeBlock?.status === 'completed') {
    showNotify("Session completed. Click 'Again' or add new task.");
    return;
  }
  timerStore.toggleTimer();
};

const handleRepeatBlock = (block: TimeBlock, index: number) => {
  timerStore.repeatBlock(block, index);
  showNotify("Task duplicated.");
};

const onTabChange = (index: number) => {
  selectedTabIndex.value = index;
};

// --- 视觉计算 (保持在组件内，负责渲染) ---
const r = 150;
const circumference = 2 * Math.PI * r;

const strokeOffset = computed(() => {
  if (!timerStore.activeBlock) return circumference;

  const elapsed = timerStore.activeBlock.elapsed || 0;
  const remaining = timerStore.activeBlock.remainingTime || 0;
  const totalEffective = elapsed + remaining;

  if (totalEffective === 0) return circumference;
  return circumference - (elapsed / totalEffective) * circumference;
});

const formattedTime = computed(() => {
  if (!timerStore.activeBlock) return '00:00';
  return formattedTimeBlock(timerStore.activeBlock.remainingTime);
});

const formattedTimeBlock = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

const currentBlockLabel = computed(() => {
  if (!timerStore.activeBlock) return 'IDLE';
  if (timerStore.activeBlock.type === 'focus') return 'DEEP FOCUS';
  return 'RECHARGE';
});

const currentBlockColorClass = computed(() => {
  switch (timerStore.activeBlock?.type) {
    case 'focus':
      return 'text-primary';
    case 'shortBreak':
      return 'text-green-400';
    case 'longBreak':
      return 'text-purple-400';
    default:
      return 'text-text-muted';
  }
});

const currentBlockStrokeClass = computed(() => {
  switch (timerStore.activeBlock?.type) {
    case 'focus':
      return 'stroke-primary';
    case 'shortBreak':
      return 'stroke-green-400';
    case 'longBreak':
      return 'stroke-purple-400';
    default:
      return 'stroke-gray-700';
  }
});

const estimatedFinishTime = computed(() => {
  if (!timerStore.activeBlock) return '--:--';
  const now = new Date();
  let totalSecondsLeft = timerStore.activeBlock.remainingTime;
  for (let i = timerStore.activeBlockIndex + 1; i < timerStore.timeline.length; i++) {
    totalSecondsLeft += timerStore.timeline[i].duration * 60;
  }
  const finishTime = new Date(now.getTime() + totalSecondsLeft * 1000);
  return `${finishTime.getHours().toString().padStart(2, '0')}:${finishTime.getMinutes().toString().padStart(2, '0')}`;
});

// 计算属性绑定 Input
const currentBlockDurationInput = computed({
  get: () => timerStore.activeBlock ? Math.round(timerStore.activeBlock.remainingTime / 60) : 0,
  set: (val: number) => {
    if (timerStore.activeBlock && timerStore.activeBlock.status !== 'completed') {
      timerStore.activeBlock.remainingTime = val * 60;
    }
  }
});

// UI Event Handlers
const onBlockClick = (index: number) => {
  if (timerStore.timeline[index].status === 'completed') return;
  if (timerStore.isRunning) {
    showNotify("Pause timer to switch blocks.");
    return;
  }
  timerStore.activeBlockIndex = index;
};

const onDurationChange = (block: TimeBlock) => {
  if (!timerStore.isRunning && block.status !== 'completed') {
    block.remainingTime = block.duration * 60;
    block.elapsed = 0;
  }
};

// 拖拽逻辑 (直接操作 Store State，Pinia 支持)
let draggedItemIndex: number | null = null;
const onDragStart = (_e: DragEvent, index: number) => {
  if (timerStore.isRunning) return;
  if (timerStore.timeline[index].status === 'completed') return;
  draggedItemIndex = index;
};
const onDrop = (_e: DragEvent, index: number) => {
  if (timerStore.isRunning) return;
  if (draggedItemIndex === null || draggedItemIndex === index) return;
  if (timerStore.timeline[draggedItemIndex].status === 'completed') return;

  const item = timerStore.timeline.splice(draggedItemIndex, 1)[0];
  timerStore.timeline.splice(index, 0, item);

  if (draggedItemIndex === timerStore.activeBlockIndex) {
    timerStore.activeBlockIndex = index;
  } else if (draggedItemIndex < timerStore.activeBlockIndex && index >= timerStore.activeBlockIndex) {
    timerStore.activeBlockIndex--;
  } else if (draggedItemIndex > timerStore.activeBlockIndex && index <= timerStore.activeBlockIndex) {
    timerStore.activeBlockIndex++;
  }
  draggedItemIndex = null;
};

onMounted(async () => {
  timerStore.init(); // 恢复数据
  await flowSessionStore.fetchSessionHistory(); // 获取历史
  isSystemReady.value = true;
});
</script>

<style scoped>
.text-shadow-glow {
  text-shadow: 0 0 30px currentColor;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
