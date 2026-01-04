<!-- src/views/forum/components/CreatePostModal.vue -->
<script lang="ts" setup>
import {ref} from 'vue'
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot} from '@headlessui/vue'
import {useForumStore} from '@/stores/forumStore/forum'
import {useTeamsStore} from '@/stores/teams'
import {toast} from 'vue-sonner'
import MarkdownEditor from '@/components/share/MarkdownEditor.vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits(['close'])
const forumStore = useForumStore()
const teamsStore = useTeamsStore()

const form = ref({
  title: '',
  content: ''
})

const handleSubmit = async () => {
  if (!form.value.title || !form.value.content) {
    toast.warning('Please provide both title and content.')
    return
  }

  if (!teamsStore.currentTeamId || !forumStore.currentSectionId) return

  try {
    await forumStore.addPost(teamsStore.currentTeamId, forumStore.currentSectionId, form.value)
    toast.success('Post published successfully!')
    form.value = {title: '', content: ''}
    emit('close')
  } catch (error) {
    toast.error('Failed to publish post.')
  }
}
</script>

<template>
  <TransitionRoot :show="isOpen" appear as="template">
    <Dialog as="div" class="relative z-50" @close="emit('close')">
      <!-- Overlay -->
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-bg-main/80 backdrop-blur-md"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <!--
            ✅ 修复：移除 as="template"，让其渲染为 div。
            添加 w-full max-w-5xl 确保动画容器有宽度。
          -->
          <TransitionChild
            as="div"
            class="w-full max-w-5xl"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95 translate-y-4"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-95 translate-y-4"
          >
            <!-- Panel Card -->
            <DialogPanel
              class="w-full h-[85vh] flex flex-col transform overflow-hidden rounded-2xl bg-bg-card border border-border/20 shadow-2xl transition-all">

              <!-- Header -->
              <div class="px-6 py-4 border-b border-border/10 flex items-center justify-between shrink-0 bg-surface/30">
                <DialogTitle as="h3" class="text-lg font-bold flex items-center gap-2">
                  <i class="i-carbon-pen-fountain text-primary"/>
                  Draft new discussion
                </DialogTitle>
                <div class="flex gap-2">
                  <button class="btn-ghost text-xs" @click="emit('close')">Cancel</button>
                  <button
                    :disabled="forumStore.loading.action || !form.title"
                    class="btn-primary text-xs py-1.5"
                    @click="handleSubmit"
                  >
                    <i v-if="forumStore.loading.action" class="i-carbon-circle-dash animate-spin"/>
                    <span>Publish</span>
                  </button>
                </div>
              </div>

              <!-- Body -->
              <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
                <!-- Title Input -->
                <div class="px-6 py-4 shrink-0">
                  <input
                    v-model="form.title"
                    autofocus
                    class="w-full bg-transparent text-2xl font-bold text-text placeholder:text-muted/40 outline-none border-b border-transparent focus:border-border/20 pb-2 transition-colors"
                    placeholder="Type your title here..."
                    type="text"
                  />
                </div>

                <!-- Markdown Editor -->
                <div class="flex-1 min-h-0 relative border-t border-border/10">
                  <MarkdownEditor v-model="form.content" placeholder="Write something amazing..."/>
                </div>
              </div>

            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
