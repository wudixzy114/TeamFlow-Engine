<!-- src/views/forum/components/PostDetail.vue -->
<script lang="ts" setup>
import {ref, onMounted, computed, nextTick} from 'vue'
import {useForumStore} from '@/stores/forumStore/forum'
import {useTeamsStore} from '@/stores/teams'
import {usePreferencesStore} from '@/stores/markdown/preferences'
import {format, formatDistanceToNow} from 'date-fns'
import {toast} from 'vue-sonner'
import {Menu, MenuButton, MenuItems, MenuItem} from '@headlessui/vue'
import MarkdownReader from '@/components/share/MarkdownReader.vue'
import MarkdownIt from 'markdown-it' // 用于简单的评论渲染

const forumStore = useForumStore()
const teamsStore = useTeamsStore()
const prefStore = usePreferencesStore()
const commentInput = ref('')
const commentsContainerRef = ref<HTMLElement | null>(null)

// 简易 Markdown 渲染器用于评论 (不需要太复杂的代码高亮，保持轻量)
const commentMd = new MarkdownIt({linkify: true, breaks: true})

const currentTeamId = computed(() => teamsStore.currentTeamId)

// 主题列表 (复用)
const MD_THEMES = [
  {value: 'default', label: 'Glass', colorClass: 'bg-gray-500'},
  {value: 'github', label: 'Light', colorClass: 'bg-white'},
  {value: 'github-dark', label: 'Dark', colorClass: 'bg-[#0d1117]'},
  {value: 'notion', label: 'Notion', colorClass: 'bg-orange-50'},
]

onMounted(() => {
  if (forumStore.currentPost && currentTeamId.value) {
    forumStore.fetchComments(currentTeamId.value, forumStore.currentPost.id)
  }
})

const handleBack = () => {
  forumStore.currentPost = null
}

const handleLike = async () => {
  if (forumStore.currentPost && currentTeamId.value) {
    await forumStore.togglePostLike(currentTeamId.value, forumStore.currentPost)
  }
}

const submitComment = async () => {
  if (!commentInput.value.trim() || !forumStore.currentPost || !currentTeamId.value) return
  try {
    await forumStore.addComment(currentTeamId.value, forumStore.currentPost.id, commentInput.value)
    commentInput.value = ''
    toast.success('Reply posted')

    // 滚动到底部
    nextTick(() => {
      if (commentsContainerRef.value) {
        commentsContainerRef.value.scrollIntoView({behavior: 'smooth', block: 'end'})
      }
    })
  } catch (e) {
    toast.error('Failed to comment')
  }
}

const handleDeletePost = async () => {
  if (!confirm('Delete this post?')) return
  if (forumStore.currentPost && currentTeamId.value) {
    try {
      await forumStore.removePost(currentTeamId.value, forumStore.currentPost.id)
      forumStore.currentPost = null
      toast.success('Post deleted')
    } catch (e) {
      toast.error('Failed to delete')
    }
  }
}

const renderComment = (content: string) => {
  return commentMd.render(content)
}
</script>

<template>
  <div v-if="forumStore.currentPost" class="animate-enter h-full flex flex-col relative bg-bg">

    <!-- 1. Scrollable Content Area -->
    <div class="flex-1 overflow-y-auto scrollbar-hide pb-32"> <!-- pb-32 为底部固定栏留出空间 -->

      <!-- Top Navigation & Actions -->
      <div class="sticky top-0 z-20 bg-bg/80 backdrop-blur-md border-b border-border/10 px-6 py-3 flex-between">
        <button class="btn-ghost pl-0 text-muted hover:text-primary gap-2 group text-sm" @click="handleBack">
          <i class="i-carbon-arrow-left text-lg group-hover:-translate-x-1 transition-transform"/>
          <span>Back</span>
        </button>

        <div class="flex items-center gap-2">
          <!-- 主题切换 -->
          <Menu as="div" class="relative inline-block text-left">
            <MenuButton class="btn-ghost p-1.5 text-muted hover:text-text" title="Reading Theme">
              <i class="i-carbon-color-palette text-lg"/>
            </MenuButton>
            <transition
              enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0"
              enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0"
            >
              <MenuItems
                class="absolute right-0 mt-2 w-32 origin-top-right divide-y divide-border/20 rounded-xl bg-bg-card border border-border/50 shadow-glow-lg ring-1 ring-black/5 focus:outline-none z-50">
                <div class="p-1">
                  <MenuItem v-for="theme in MD_THEMES" :key="theme.value" v-slot="{ active }">
                    <button
                      :class="[active ? 'bg-primary/10 text-primary' : 'text-text-main', 'group flex w-full items-center rounded-lg px-2 py-1.5 text-xs transition-colors']"
                      @click="prefStore.markdownTheme = theme.value"
                    >
                      <span :class="['w-2 h-2 rounded-full mr-2 border border-border/50', theme.colorClass]"></span>
                      {{ theme.label }}
                    </button>
                  </MenuItem>
                </div>
              </MenuItems>
            </transition>
          </Menu>

          <!-- 只有作者或管理员可见 -->
          <button
            v-if="forumStore.currentPost.author.id === teamsStore.currentTeamDetail?.owner?.id"
            class="btn-ghost text-muted hover:text-error p-1.5"
            @click="handleDeletePost"
          >
            <i class="i-carbon-trash-can text-lg"/>
          </button>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 md:px-10 py-8">
        <!-- Post Header -->
        <header class="mb-8">
          <h1 class="text-3xl md:text-4xl font-bold text-text mb-6 leading-tight tracking-tight">
            {{ forumStore.currentPost.title }}
          </h1>

          <div class="flex items-center gap-4">
            <div
              class="w-10 h-10 rounded-full bg-surface border border-border/20 flex-center text-sm font-bold shadow-inner text-primary">
              {{ forumStore.currentPost.author.username?.[0]?.toUpperCase() }}
            </div>
            <div>
              <div class="text-text font-medium">
                {{ forumStore.currentPost.author.nickname || forumStore.currentPost.author.username }}
              </div>
              <div class="text-xs text-muted flex items-center gap-2">
                <span>{{ format(new Date(forumStore.currentPost.created_at), 'MMM dd, yyyy') }}</span>
                <span class="w-1 h-1 rounded-full bg-border"></span>
                <span>{{ format(new Date(forumStore.currentPost.created_at), 'HH:mm') }}</span>
              </div>
            </div>
          </div>
        </header>

        <!-- Markdown Reader Content -->
        <div class="glass-panel p-1 rounded-2xl overflow-hidden shadow-sm border border-border/10 mb-12">
          <MarkdownReader :content="forumStore.currentPost.content"/>
        </div>

        <!-- Post Stats Bar -->
        <div class="flex items-center gap-4 py-4 border-t border-b border-border/10 mb-10">
          <button
            :class="forumStore.currentPost.liked_by_current_user
              ? 'bg-primary/10 border-primary/20 text-primary'
              : 'bg-surface/50 border-transparent text-muted hover:bg-surface hover:text-text'"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all duration-200 border"
            @click="handleLike"
          >
            <i
              :class="forumStore.currentPost.liked_by_current_user ? 'i-carbon-thumbs-up-filled' : 'i-carbon-thumbs-up'"
              class="text-lg transition-transform active:scale-125"/>
            <span class="font-medium text-sm">{{ forumStore.currentPost.likes_count }}</span>
          </button>

          <div class="text-sm text-muted">
            <span class="font-medium text-text">{{ forumStore.comments.length }}</span> comments
          </div>
        </div>

        <!-- Comments List -->
        <div ref="commentsContainerRef" class="space-y-8">
          <div v-if="forumStore.loading.comments" class="text-center py-8 text-muted italic flex-center gap-2">
            <i class="i-carbon-circle-dash animate-spin"/> Loading discussion...
          </div>

          <div v-else-if="forumStore.comments.length === 0" class="text-center py-10 text-muted opacity-60">
            <i class="i-carbon-chat-bot text-4xl mb-2 block mx-auto"/>
            No comments yet. Start the conversation!
          </div>

          <div
            v-for="comment in forumStore.comments"
            :key="comment.id"
            class="flex gap-4 group animate-enter"
          >
            <div
              class="w-8 h-8 rounded-full bg-surface border border-border/10 shrink-0 flex-center text-xs font-bold text-muted mt-1">
              {{ comment.user.username?.[0]?.toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-semibold text-sm text-text">{{
                    comment.user.nickname || comment.user.username
                  }}</span>
                <span class="text-[10px] text-muted opacity-60">{{ formatDistanceToNow(new Date(comment.created_at)) }} ago</span>
              </div>

              <!-- 优化后的评论气泡 -->
              <div
                class="bg-surface/40 border border-border/5 px-4 py-2.5 rounded-2xl rounded-tl-none inline-block max-w-full hover:bg-surface/60 transition-colors">
                <!-- 使用 v-html 渲染简单的 markdown -->
                <div class="prose prose-sm prose-invert max-w-none text-text/90 leading-relaxed text-sm break-words"
                     v-html="renderComment(comment.content)"></div>
              </div>

              <!-- Delete Btn -->
              <div class="mt-1 h-5">
                <button
                  v-if="comment.user.id === teamsStore.currentTeamDetail?.owner?.id /* 或者是当前用户 */"
                  class="text-[10px] text-muted hover:text-error opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                  @click="teamsStore.currentTeamId && forumStore.removeComment(teamsStore.currentTeamId, comment.id)"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. Sticky Comment Input Bar -->
    <div class="absolute bottom-0 left-0 right-0 p-4 z-30 pointer-events-none">
      <div class="max-w-4xl mx-auto pointer-events-auto">
        <div
          class="glass-panel p-2 pl-4 rounded-full flex items-center gap-3 shadow-2xl border border-white/10 ring-1 ring-black/5">
          <div
            class="w-8 h-8 rounded-full bg-gradient-to-tr from-primary/80 to-secondary/80 flex-center shrink-0 shadow-lg">
            <i class="i-carbon-user-avatar-filled text-white text-lg"/>
          </div>

          <input
            v-model="commentInput"
            class="flex-1 bg-transparent border-none outline-none text-sm text-text placeholder:text-muted/60 h-10"
            placeholder="Share your thoughts..."
            type="text"
            @keydown.enter="submitComment"
          />

          <button
            :disabled="!commentInput.trim() || forumStore.loading.action"
            class="w-10 h-10 rounded-full bg-primary flex-center text-white hover:bg-primary-active disabled:opacity-50 disabled:bg-surface transition-all active:scale-90 shadow-lg"
            @click="submitComment"
          >
            <i v-if="forumStore.loading.action" class="i-carbon-circle-dash animate-spin"/>
            <i v-else class="i-carbon-send-alt"/>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
