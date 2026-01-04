<!-- src/components/highlights/HighlightDetail.vue -->
<script lang="ts" setup>
import {ref, computed, watch} from 'vue'
import {useHighlightsStore} from '@/stores/highlights'
import {useTeamsStore} from '@/stores/teams'
import {Dialog, DialogPanel, TransitionChild, TransitionRoot} from '@headlessui/vue'

const props = defineProps<{
  highlightId: string | null
}>()

const emit = defineEmits(['close'])

const store = useHighlightsStore()
const teamsStore = useTeamsStore()
const commentInput = ref('')

// 获取当前高光对象
const currentHighlight = computed(() =>
  store.highlights.find(h => h.id === props.highlightId)
)

// 当 ID 变化时拉取评论
watch(() => props.highlightId, async (newId) => {
  if (newId) {
    commentInput.value = ''
    await store.fetchComments(newId)
  }
})

const getUserName = (userOrId: any) => {
  if (!userOrId) return 'Unknown'

  if (typeof userOrId === 'object' && userOrId.username) {
    return userOrId.nickname || userOrId.username
  }

  if (typeof userOrId === 'string') {
    const member = teamsStore.currentTeamDetail?.members.find(m => m.id === userOrId)
    return member ? (member.nickname || member.username) : 'Unknown User'
  }

  return 'Unknown'
}

const getUserInitial = (userOrId: any) => {
  const name = getUserName(userOrId)
  return name[0]?.toUpperCase() || '?'
}

// 发送评论
const handleSendComment = async () => {
  if (!commentInput.value.trim() || !props.highlightId) return
  await store.addComment(props.highlightId, commentInput.value)
  commentInput.value = ''
}

const handleLike = () => {
  if (props.highlightId) store.toggleLike(props.highlightId)
}
</script>

<template>
  <TransitionRoot :show="!!highlightId" as="template">
    <Dialog as="div" class="relative z-[200]" @close="emit('close')">
      <!-- 遮罩：让背景的 3D 星系变暗、模糊 -->
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-bg-main/60 backdrop-blur-md transition-opacity"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-hidden">
        <div class="absolute inset-0 overflow-hidden">
          <div class="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
            <TransitionChild
              as="template"
              enter="transform transition ease-in-out duration-500 sm:duration-700"
              enter-from="translate-x-full"
              enter-to="translate-x-0"
              leave="transform transition ease-in-out duration-500 sm:duration-700"
              leave-from="translate-x-0"
              leave-to="translate-x-full"
            >
              <DialogPanel class="pointer-events-auto w-screen max-w-md">
                <!-- 侧边栏容器 -->
                <div class="flex h-full flex-col overflow-y-scroll bg-bg-card border-l border-border shadow-2xl">

                  <!-- 头部 -->
                  <div class="px-6 py-6 border-b border-border bg-bg-surface/50">
                    <div class="flex items-start justify-between">
                      <h2 class="text-h2 text-gradient">Highlight Detail</h2>
                      <button class="btn-ghost p-2 rounded-full hover:bg-white/10" @click="emit('close')">
                        <div class="i-carbon-close text-xl"></div>
                      </button>
                    </div>
                  </div>

                  <!-- 内容区 -->
                  <div v-if="currentHighlight" class="relative flex-1 px-6 py-6">
                    <!-- 作者信息 -->
                    <div class="flex items-center gap-3 mb-4">
                      <div
                        class="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex-center text-white font-bold">
                        {{ getUserInitial(currentHighlight.user) }}
                      </div>
                      <div>
                        <div class="font-medium text-text-main">{{ getUserName(currentHighlight.user) }}</div>
                        <div class="text-xs text-text-muted">{{
                            new Date(currentHighlight.created_at).toLocaleString()
                          }}
                        </div>
                      </div>
                    </div>

                    <!-- 高光正文 -->
                    <div class="text-lg text-text-main leading-relaxed whitespace-pre-wrap mb-8 font-light">
                      {{ currentHighlight.content }}
                    </div>

                    <!-- 操作栏 -->
                    <div class="flex items-center gap-4 mb-8 border-y border-white/5 py-3">
                      <button
                        :class="currentHighlight.liked_by_current_user ? 'text-rose-500' : ''"
                        class="btn-ghost text-sm gap-2"
                        @click="handleLike"
                      >
                        <div
                          :class="currentHighlight.liked_by_current_user ? 'i-carbon-favorite-filled' : 'i-carbon-favorite'"
                          class="text-lg"></div>
                        {{ currentHighlight.likes_count }} Likes
                      </button>
                      <div class="text-text-muted text-sm flex items-center gap-2">
                        <div class="i-carbon-chat text-lg"></div>
                        {{ store.commentsMap[currentHighlight.id]?.length || 0 }} Comments
                      </div>
                    </div>

                    <!-- 评论列表 -->
                    <div class="space-y-6">
                      <h3 class="text-sm font-bold text-text-muted uppercase tracking-wider">Discussion</h3>

                      <div v-if="store.loadingCommentsMap[currentHighlight.id]" class="flex-center py-4">
                        <div class="i-carbon-circle-dash animate-spin text-2xl text-primary"></div>
                      </div>

                      <ul v-else class="space-y-4">
                        <li v-for="comment in store.commentsMap[currentHighlight.id]" :key="comment.id"
                            class="flex gap-3 animate-fade-in">
                          <div
                            class="w-8 h-8 rounded-full bg-bg-surface flex-center text-xs text-text-muted flex-shrink-0 border border-white/10">
                            {{ getUserInitial(comment.user_id) }}
                          </div>
                          <div class="flex-1 bg-bg-surface/30 rounded-xl p-3 border border-white/5">
                            <div class="flex justify-between items-baseline mb-1">
                              <span class="text-sm font-medium text-text-main">{{ getUserName(comment.user_id) }}</span>
                              <span class="text-[10px] text-text-muted opacity-60">{{
                                  new Date(comment.created_at).toLocaleDateString()
                                }}</span>
                            </div>
                            <p class="text-sm text-text-muted/90">{{ comment.content }}</p>
                          </div>
                        </li>
                      </ul>
                    </div>
                  </div>

                  <!-- 底部评论输入框 -->
                  <div class="border-t border-border p-4 bg-bg-surface/80 backdrop-blur pb-8">
                    <div class="relative">
                      <textarea
                        v-model="commentInput"
                        class="input-base resize-none pr-12 min-h-[50px]"
                        placeholder="Share your thoughts..."
                        rows="2"
                        @keydown.ctrl.enter="handleSendComment"
                      ></textarea>
                      <button
                        :disabled="!commentInput.trim()"
                        class="absolute right-2 bottom-2 p-1.5 rounded-lg text-primary hover:bg-primary/10 transition-colors disabled:opacity-30"
                        @click="handleSendComment"
                      >
                        <div class="i-carbon-send-alt text-xl"></div>
                      </button>
                    </div>
                  </div>

                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
