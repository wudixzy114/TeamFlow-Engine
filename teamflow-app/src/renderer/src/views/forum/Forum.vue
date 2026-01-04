<!-- src/views/forum/ForumLayout.vue -->
<script lang="ts" setup>
import {onMounted, ref, computed, watch} from 'vue'
import {useForumStore} from '@/stores/forumStore/forum'
import {useTeamsStore} from '@/stores/teams'
import CreateSectionModal from '@/components/forum/CreateSectionModal.vue'
import PostList from '@/components/forum/PostList.vue'
import PostDetail from '@/components/forum/PostDetail.vue'

const forumStore = useForumStore()
const teamsStore = useTeamsStore()

// State
const isCreateSectionOpen = ref(false)
const searchQuery = computed({
  get: () => forumStore.searchQuery,
  set: (val) => forumStore.searchQuery = val
})

// Computed
const currentTeamId = computed(() => teamsStore.currentTeamId)
const isOwner = computed(() => teamsStore.isCurrentUserOwner)

// --- Lifecycle & Watch ---

// 1. 挂载时拉取数据
onMounted(() => {
  if (currentTeamId.value) {
    initForumData(currentTeamId.value)
  }
})

// 2. 监听 Team ID 变化（处理用户在侧边栏切换团队的情况）
watch(currentTeamId, (newId) => {
  if (newId) {
    initForumData(newId)
  }
})

// 初始化数据逻辑
const initForumData = async (teamId: string) => {
  forumStore.currentPost = null
  forumStore.currentSectionId = null
  await forumStore.fetchSections(teamId)

  // 如果有版块，默认选中第一个
  if (forumStore.sections.length > 0) {
    handleSectionClick(forumStore.sections[0].id)
  }
}

const handleSectionClick = (sectionId: string) => {
  if (!currentTeamId.value) return
  forumStore.fetchPosts(currentTeamId.value, sectionId)
  forumStore.currentPost = null // 确保返回列表模式
}

// 视图切换逻辑
const currentViewComponent = computed(() => {
  return forumStore.currentPost ? PostDetail : PostList
})
</script>

<template>
  <div class="flex h-full w-full overflow-hidden bg-bg text-text transition-colors duration-300">

    <!-- Left Sidebar: Connection Hub -->
    <aside class="w-64 flex flex-col border-r border-border/10 bg-surface/30 backdrop-blur-md transition-all">
      <!-- Header -->
      <div class="h-16 flex items-center justify-between px-5 border-b border-border/10 shrink-0">
        <div class="flex items-center gap-2 text-primary">
          <i class="i-carbon-catalog text-xl"/>
          <span class="font-bold tracking-tight text-lg">Forum</span>
        </div>

        <!--
             ✨ 修改：将添加版块按钮移到这里，更加明显
             只有 Owner 可见
        -->
        <button
          v-if="isOwner"
          class="w-7 h-7 flex-center rounded hover:bg-surface text-muted hover:text-primary transition-colors"
          title="Create New Channel"
          @click="isCreateSectionOpen = true"
        >
          <i class="i-carbon-add text-lg"/>
        </button>
      </div>

      <!-- Section List -->
      <div class="flex-1 overflow-y-auto py-4 px-3 space-y-1 scrollbar-hide">
        <div class="text-[10px] font-bold text-muted uppercase tracking-wider px-3 mb-2 opacity-60">
          Channels
        </div>

        <!-- Loading Skeletons -->
        <template v-if="forumStore.loading.sections">
          <div v-for="i in 3" :key="i"
               class="h-9 mx-2 rounded-lg bg-surface/50 animate-pulse my-1 border border-transparent"></div>
        </template>

        <!-- Channel List -->
        <template v-else>
          <button
            v-for="section in forumStore.sections"
            :key="section.id"
            :class="forumStore.currentSectionId === section.id
              ? 'bg-primary/10 text-primary font-medium border-primary/10'
              : 'text-muted hover:text-text hover:bg-surface/60'"
            class="w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-3 transition-all duration-200 group relative overflow-hidden border border-transparent"
            @click="handleSectionClick(section.id)"
          >
            <!-- Icon -->
            <i class="i-carbon-hashtag text-sm opacity-70 group-hover:opacity-100 transition-opacity"/>

            <!-- Name -->
            <span class="truncate text-sm">{{ section.name }}</span>

            <!-- Active Indicator (Right side) -->
            <div
              v-if="forumStore.currentSectionId === section.id"
              class="absolute right-2 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgb(var(--c-primary))]"
            ></div>
          </button>
        </template>

        <!-- Empty State -->
        <div v-if="!forumStore.loading.sections && forumStore.sections.length === 0" class="px-4 py-8 text-center">
          <div class="text-xs text-muted mb-2">No channels found.</div>
          <button
            v-if="isOwner"
            class="text-xs text-primary hover:underline"
            @click="isCreateSectionOpen = true"
          >
            Create one?
          </button>
        </div>
      </div>

      <!-- ✨ 已移除 User Status Area -->
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col min-w-0 relative bg-bg">
      <!-- Top Bar -->
      <header
        class="h-16 border-b border-border/10 flex items-center justify-between px-6 bg-bg/80 backdrop-blur-xl z-10 sticky top-0">
        <div class="flex items-center gap-4 flex-1">
          <!-- Search -->
          <div class="relative group w-full max-w-md transition-all duration-300 focus-within:max-w-lg">
            <i
              class="i-carbon-search absolute left-3 top-1/2 -translate-y-1/2 text-muted group-focus-within:text-primary transition-colors text-lg"/>
            <input
              v-model="searchQuery"
              class="input-base pl-10 bg-surface/30 border-transparent focus:bg-surface focus:border-primary/30 h-10 w-full transition-all"
              placeholder="Search discussions..."
              type="text"
            />
            <!-- Clear Button -->
            <button
              v-if="searchQuery"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text"
              @click="searchQuery = ''"
            >
              <i class="i-carbon-close"/>
            </button>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button class="btn-ghost p-2 text-muted hover:text-text" title="Filter View">
            <i class="i-carbon-settings-adjust text-xl"/>
          </button>
        </div>
      </header>

      <!-- Dynamic Content -->
      <div class="flex-1 overflow-y-auto relative scrollbar-hide p-6 md:p-8">
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 -translate-y-2"
          mode="out-in"
        >
          <component :is="currentViewComponent" class="max-w-5xl mx-auto w-full"/>
        </Transition>
      </div>
    </main>

    <!-- Modals -->
    <CreateSectionModal
      :is-open="isCreateSectionOpen"
      @close="isCreateSectionOpen = false"
    />
  </div>
</template>
