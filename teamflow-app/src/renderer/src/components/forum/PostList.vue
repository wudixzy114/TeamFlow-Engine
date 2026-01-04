<script lang="ts" setup>
import {ref, computed} from 'vue'
import {useForumStore} from '@/stores/forumStore/forum'
import {useTeamsStore} from '@/stores/teams'
import CreatePostModal from '@/components/forum/CreatePostModal.vue'
import {formatDistanceToNow} from 'date-fns'

const forumStore = useForumStore()
const teamsStore = useTeamsStore()
const isCreatePostOpen = ref(false)

// Helpers
const currentSection = computed(() =>
  forumStore.sections.find(s => s.id === forumStore.currentSectionId)
)

const openPost = (post: any) => {
  if (!teamsStore.currentTeamId) return
  forumStore.fetchPostDetail(teamsStore.currentTeamId, post.id)
}

const formatDate = (dateStr: string) => {
  try {
    return formatDistanceToNow(new Date(dateStr), {addSuffix: true})
  } catch (e) {
    return ''
  }
}

// 简单的纯文本摘要提取
const getExcerpt = (markdown: string) => {
  return markdown
    .replace(/[#*`>]/g, '') // 去除 Markdown 符号
    .replace(/\[(.*?)]\(.*?\)/g, '$1') // 替换链接
    .slice(0, 150) + (markdown.length > 150 ? '...' : '')
}
</script>

<template>
  <div class="space-y-6 pb-20">
    <!-- Section Header -->
    <div class="flex-between animate-enter">
      <div>
        <h1 class="text-3xl font-bold text-text mb-2 flex items-center gap-2">
          <span class="text-primary opacity-80">#</span>
          {{ currentSection?.name || 'Select a Channel' }}
        </h1>
        <p class="text-muted text-sm max-w-2xl">
          {{ currentSection?.description || 'Join the conversation and share your ideas.' }}
        </p>
      </div>
      <button
        v-if="forumStore.currentSectionId"
        class="btn-primary"
        @click="isCreatePostOpen = true"
      >
        <i class="i-carbon-pen text-lg"/>
        <span>New Post</span>
      </button>
    </div>

    <!-- Search Empty State -->
    <div v-if="forumStore.searchQuery && forumStore.filteredPosts.length === 0"
         class="flex-center flex-col py-20 text-muted animate-enter">
      <div class="i-carbon-search-locate text-4xl mb-4 opacity-30"/>
      <p>No results found for "{{ forumStore.searchQuery }}"</p>
      <button class="text-primary text-sm mt-2 hover:underline" @click="forumStore.searchQuery = ''">Clear search
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="!forumStore.loading.posts && forumStore.posts.length === 0"
         class="flex-center flex-col py-24 text-muted animate-enter">
      <div class="w-24 h-24 rounded-full bg-surface/50 flex-center mb-6 border border-border/10 shadow-inner">
        <i class="i-carbon-chat text-5xl opacity-20"/>
      </div>
      <p class="text-lg font-medium">No posts here yet.</p>
      <p class="text-sm opacity-60">Be the first to share your thoughts!</p>
    </div>

    <!-- Skeleton Loading -->
    <div v-else-if="forumStore.loading.posts && forumStore.posts.length === 0" class="space-y-4">
      <div v-for="i in 4" :key="i" class="h-36 bg-surface/30 rounded-2xl animate-pulse border border-border/5"></div>
    </div>

    <!-- Post List -->
    <div v-else class="grid gap-4">
      <article
        v-for="(post, index) in forumStore.filteredPosts"
        :key="post.id"
        :style="{ animationDelay: `${index * 50}ms` }"
        class="card-interactive p-6 group flex flex-col gap-3 relative overflow-hidden"
        @click="openPost(post)"
      >
        <!-- Highlight Bar -->
        <div
          class="absolute left-0 top-0 bottom-0 w-1 bg-primary/0 group-hover:bg-primary transition-colors duration-300"></div>

        <!-- Header -->
        <div class="flex justify-between items-start pl-2">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-full bg-surface border border-border/20 flex-center text-primary font-bold shadow-sm shrink-0">
              {{ post.author.username?.charAt(0).toUpperCase() || 'U' }}
            </div>
            <div>
              <h3 class="text-xl font-semibold text-text leading-tight group-hover:text-primary transition-colors">
                {{ post.title }}
              </h3>
              <div class="flex items-center gap-2 text-xs text-muted mt-1">
                <span class="font-medium text-text/80">{{ post.author.nickname || post.author.username }}</span>
                <span class="w-1 h-1 rounded-full bg-border/50"></span>
                <span class="flex items-center gap-1">
                  <i class="i-carbon-time"/> {{ formatDate(post.created_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Preview Content -->
        <p class="text-muted line-clamp-2 text-sm leading-relaxed pl-13 pr-4 opacity-80">
          {{ getExcerpt(post.content) }}
        </p>

        <!-- Footer / Stats -->
        <div class="flex items-center gap-6 mt-2 pl-13 text-sm text-muted">
          <div
            :class="post.liked_by_current_user ? 'text-primary' : ''"
            class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-surface transition-colors"
          >
            <i :class="post.liked_by_current_user ? 'i-carbon-thumbs-up-filled' : 'i-carbon-thumbs-up'"
               class="text-base"/>
            <span>{{ post.likes_count }}</span>
          </div>
          <div class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-surface hover:text-text transition-colors">
            <i class="i-carbon-chat text-base"/>
            <span>{{ post.comments_count }}</span>
          </div>
        </div>
      </article>

      <!-- Load More -->
      <div v-if="forumStore.postPagination.hasMore" class="flex-center pt-8 pb-4">
        <button
          :disabled="forumStore.loading.posts"
          class="btn-outline text-xs px-6 py-2 rounded-full"
          @click="teamsStore.currentTeamId && forumStore.fetchPosts(teamsStore.currentTeamId, forumStore.currentSectionId!, true)"
        >
          <i v-if="forumStore.loading.posts" class="i-carbon-circle-dash animate-spin text-lg"/>
          <span v-else>Load older posts</span>
        </button>
      </div>
    </div>

    <CreatePostModal
      :is-open="isCreatePostOpen"
      @close="isCreatePostOpen = false"
    />
  </div>
</template>
