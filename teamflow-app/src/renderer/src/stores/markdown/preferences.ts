import {defineStore} from 'pinia';

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    markdownTheme: 'default',
  }),
  persist: true,
});
