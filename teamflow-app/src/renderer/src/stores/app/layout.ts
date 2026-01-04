import {defineStore} from 'pinia'
import {ref} from 'vue'

export const useLayoutStore = defineStore('layout', () => {
  const isSidebarCollapsed = ref(false)

  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }

  function setSidebarCollapse(state: boolean) {
    isSidebarCollapsed.value = state
  }

  return {
    isSidebarCollapsed,
    toggleSidebar,
    setSidebarCollapse
  }
})
