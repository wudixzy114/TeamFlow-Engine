import {defineStore} from 'pinia'
import {useColorMode, useCycleList} from '@vueuse/core'
import {computed} from 'vue'

export const availableThemes = [
  'focus',
  'connection',
  'zen',
  'clean',
  'synthwave',
  'abyss'
]

export type ThemeType = typeof availableThemes[number]

export const useThemeStore = defineStore('theme', () => {
  const mode = useColorMode<ThemeType>({
    selector: 'html',
    attribute: 'data-theme',
    initialValue: 'focus',
    storageKey: 'app-theme',
    modes: {
      // 映射关系 (key: 模式名, value: 属性值)
      focus: 'focus',
      connection: 'connection',
      zen: 'zen',
      clean: 'clean',
      synthwave: 'synthwave',
      abyss: 'abyss',
    },
  })

  const {next, state, index} = useCycleList(availableThemes, {initialValue: mode});
  const nextTheme = () => {
    next()
    mode.value = state.value
  }

  const setTheme = (themeName: string) => {
    if (availableThemes.includes(themeName as ThemeType)) {
      mode.value = themeName as ThemeType
      index.value = availableThemes.indexOf(themeName as ThemeType)
    }
  }

  return {
    mode,
    nextTheme,
    setTheme,
    isDark: computed(() => mode.value !== 'clean'),
    availableThemes
  }
})


