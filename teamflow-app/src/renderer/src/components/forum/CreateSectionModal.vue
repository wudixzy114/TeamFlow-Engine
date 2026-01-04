<!-- src/views/forum/components/CreateSectionModal.vue -->
<script lang="ts" setup>
import {ref} from 'vue'
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot} from '@headlessui/vue'
import {useForumStore} from '@/stores/forumStore/forum'
import {useTeamsStore} from '@/stores/teams'
import {toast} from 'vue-sonner'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits(['close'])
const forumStore = useForumStore()
const teamsStore = useTeamsStore()

const form = ref({
  name: '',
  description: ''
})

const handleSubmit = async () => {
  if (!form.value.name) return
  if (!teamsStore.currentTeamId) return

  try {
    await forumStore.addSection(teamsStore.currentTeamId, form.value)
    toast.success('Channel created successfully')
    form.value = {name: '', description: ''}
    emit('close')
  } catch (e) {
    toast.error('Failed to create channel')
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
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm"/>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <!--
             ✅ 修复：移除 as="template"
             添加 w-full max-w-md
          -->
          <TransitionChild
            as="div"
            class="w-full max-w-md"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel
              class="w-full transform rounded-xl bg-bg-card border border-border/20 p-6 shadow-2xl transition-all">
              <DialogTitle as="h3" class="text-xl font-bold text-text mb-6 flex items-center gap-2">
                <i class="i-carbon-folder-add text-primary"/>
                Create New Channel
              </DialogTitle>

              <div class="space-y-5">
                <div>
                  <label class="block text-xs uppercase font-bold text-muted mb-1.5 ml-1">Channel Name</label>
                  <div class="relative">
                    <i class="i-carbon-hashtag absolute left-3 top-1/2 -translate-y-1/2 text-muted"/>
                    <input
                      v-model="form.name"
                      class="input-base pl-9"
                      placeholder="e.g. technology"
                      type="text"
                    />
                  </div>
                </div>

                <div>
                  <label class="block text-xs uppercase font-bold text-muted mb-1.5 ml-1">Description</label>
                  <div class="relative">
                    <input
                      v-model="form.description"
                      class="input-base"
                      placeholder="What is this channel about?"
                      type="text"
                    />
                  </div>
                </div>
              </div>

              <div class="mt-8 flex justify-end gap-3">
                <button class="btn-ghost text-sm" @click="emit('close')">Cancel</button>
                <button
                  :disabled="!form.name || forumStore.loading.action"
                  class="btn-primary text-sm"
                  @click="handleSubmit"
                >
                  <i v-if="forumStore.loading.action" class="i-carbon-circle-dash animate-spin"/>
                  Create Channel
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
