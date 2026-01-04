import {defineStore} from 'pinia'
import {ref, watch} from 'vue'
import {api} from '@/api'
import {useTeamsStore} from './teams'

export const useHighlightsStore = defineStore('highlights', () => {
  const teamsStore = useTeamsStore()

  // --- State ---
  const highlights = ref<HighlightSingle[]>([])
  const isLoading = ref(false)
  const isSubmitting = ref(false)

  // 编辑状态管理（高光本身的编辑）
  const editingHighlightId = ref<string | null>(null)

  // 评论状态管理: Key 为 highlight_id，Value 为评论列表
  const commentsMap = ref<Record<string, Comment[]>>({})
  const loadingCommentsMap = ref<Record<string, boolean>>({})

  // --- Actions (Highlights) ---

  /**
   * 拉取当前团队的高光列表
   */
  async function fetchHighlights() {
    const teamId = teamsStore.currentTeamId
    if (!teamId) {
      highlights.value = []
      return
    }

    isLoading.value = true
    try {
      const data = await api.highlights.listHighlights(teamId)
      highlights.value = data.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    } catch (error) {
      console.error('Failed to fetch highlights:', error)
      highlights.value = []
      // 列表加载失败通常由 UI 展示空状态或错误页，此处选择抛出或仅记录日志视业务而定
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 发布高光
   */
  async function addHighlight(content: string) {
    const teamId = teamsStore.currentTeamId
    if (!teamId) throw new Error('No team selected')

    isSubmitting.value = true
    try {
      await api.highlights.createHighlight(teamId, {content})
      await fetchHighlights()
    } finally {
      isSubmitting.value = false
    }
  }

  /**
   * 修改高光内容
   */
  async function saveHighlight(highlightId: string, newContent: string) {
    const teamId = teamsStore.currentTeamId
    if (!teamId) throw new Error('No team selected')

    isSubmitting.value = true
    try {
      await api.highlights.updateHighlight(teamId, {id: highlightId, content: newContent})

      // 乐观更新本地数据
      const index = highlights.value.findIndex((h) => h.id === highlightId)
      if (index !== -1) {
        highlights.value[index].content = newContent
      }
      editingHighlightId.value = null
    } finally {
      isSubmitting.value = false
    }
  }

  /**
   * 删除高光
   * 注意：UI 层应先弹出确认框，确认后再调用此 Action
   */
  async function removeHighlight(highlightId: string) {
    const teamId = teamsStore.currentTeamId
    if (!teamId) throw new Error('No team selected')

    await api.highlights.deleteHighlight(teamId, {id: highlightId})

    // 更新本地状态
    highlights.value = highlights.value.filter((h) => h.id !== highlightId)
    delete commentsMap.value[highlightId]
  }

  /**
   * 点赞/取消点赞
   */
  async function toggleLike(highlightId: string) {
    const highlight = highlights.value.find((h) => h.id === highlightId)
    if (!highlight) return

    const originalLiked = highlight.liked_by_current_user
    const originalCount = highlight.likes_count

    // 乐观 UI 更新
    highlight.liked_by_current_user = !originalLiked
    highlight.likes_count += highlight.liked_by_current_user ? 1 : -1

    try {
      if (originalLiked) {
        await api.highlights.dislikeHighlight(highlightId)
      } else {
        await api.highlights.likeHighlight(highlightId)
      }
    } catch (error) {
      // 失败回滚
      highlight.liked_by_current_user = originalLiked
      highlight.likes_count = originalCount
      throw error // 抛出错误让 UI 处理（例如显示“操作失败”）
    }
  }

  // --- Actions (Comments) ---

  async function fetchComments(highlightId: string, forceRefresh = false) {
    if (!forceRefresh && commentsMap.value[highlightId]) return

    loadingCommentsMap.value[highlightId] = true
    try {
      const comments = await api.highlights.getComments(highlightId)
      commentsMap.value[highlightId] = comments.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    } catch (error) {
      console.error(`Failed to fetch comments for ${highlightId}:`, error)
      throw error
    } finally {
      loadingCommentsMap.value[highlightId] = false
    }
  }

  async function addComment(highlightId: string, content: string) {
    await api.highlights.createComment(highlightId, {content})
    // 重新拉取以获取完整数据（ID、创建时间等）
    await fetchComments(highlightId, true)
  }

  /**
   * 删除评论
   */
  async function removeComment(highlightId: string, commentId: string) {
    await api.highlights.deleteComment(highlightId, {id: commentId})

    // 乐观更新
    if (commentsMap.value[highlightId]) {
      commentsMap.value[highlightId] = commentsMap.value[highlightId].filter(c => c.id !== commentId)
    }
  }

  /**
   * 修改评论
   */
  async function editComment(highlightId: string, commentId: string, newContent: string) {
    // 传递 ID 和 Content
    await api.highlights.updateComment(highlightId, {id: commentId, content: newContent})
    // 刷新该高光的评论列表
    await fetchComments(highlightId, true)
  }

  // --- Helpers ---

  function enterEditMode(id: string) {
    editingHighlightId.value = id
  }

  function cancelEditMode() {
    editingHighlightId.value = null
  }

  // 监听团队切换，重置数据
  watch(
    () => teamsStore.currentTeamId,
    (newTeamId) => {
      if (newTeamId) {
        fetchHighlights()
        commentsMap.value = {}
        loadingCommentsMap.value = {}
      }
    },
    {immediate: true}
  )

  return {
    // State
    highlights,
    commentsMap,
    isLoading,
    isSubmitting,
    editingHighlightId,
    loadingCommentsMap,

    // Actions
    fetchHighlights,
    addHighlight,
    saveHighlight,
    removeHighlight,
    toggleLike,
    enterEditMode,
    cancelEditMode,

    // Comment Actions
    fetchComments,
    addComment,
    removeComment,
    editComment
  }
})
