import {defineStore} from 'pinia';
import {ref} from 'vue';
import * as forumApi from '@/api/forum';

export const useForumStore = defineStore('forum', () => {
  // ================= State =================
  const searchQuery = ref('');
  // 版块列表
  const sections = ref<ForumSection[]>([]);
  const currentSectionId = ref<string | null>(null);

  // 帖子列表 (当前版块)
  const posts = ref<ForumPost[]>([]);
  const postPagination = ref({
    page: 1,
    size: 20,
    hasMore: true, // 简单的分页标识
  });

  // 帖子详情
  const currentPost = ref<ForumPost | null>(null);

  // 评论列表 (当前帖子)
  const comments = ref<ForumComment[]>([]);

  // Loading 状态
  const loading = ref({
    sections: false,
    posts: false,
    detail: false,
    comments: false,
    action: false, // 用于提交/删除等操作
  });

  // ================= Actions: Sections =================

  async function fetchSections(teamId: string) {
    loading.value.sections = true;
    try {
      const data = await forumApi.getForumSections(teamId);
      sections.value = data;
    } finally {
      loading.value.sections = false;
    }
  }

  async function addSection(teamId: string, data: ForumSectionCreateRequest) {
    loading.value.action = true;
    try {
      const newSection = await forumApi.createForumSection(teamId, data);
      sections.value.push(newSection);
      return newSection;
    } finally {
      loading.value.action = false;
    }
  }

  async function editSection(teamId: string, sectionId: string, data: ForumSectionModifyRequest) {
    loading.value.action = true;
    try {
      const updatedSection = await forumApi.updateForumSection(teamId, sectionId, data);
      const index = sections.value.findIndex(s => s.id === sectionId);
      if (index !== -1) {
        sections.value[index] = updatedSection;
      }
    } finally {
      loading.value.action = false;
    }
  }

  async function removeSection(teamId: string, sectionId: string) {
    loading.value.action = true;
    try {
      await forumApi.deleteForumSection(teamId, sectionId);
      sections.value = sections.value.filter(s => s.id !== sectionId);
      if (currentSectionId.value === sectionId) {
        currentSectionId.value = null;
        posts.value = [];
      }
    } finally {
      loading.value.action = false;
    }
  }

  // ================= Actions: Posts =================

  /**
   * 加载帖子列表
   * @param teamId
   * @param sectionId
   * @param isLoadMore 是否加载更多 (true: 追加, false: 刷新)
   */
  async function fetchPosts(teamId: string, sectionId: string, isLoadMore = false) {
    if (!isLoadMore) {
      postPagination.value.page = 1;
      postPagination.value.hasMore = true;
      posts.value = [];
      currentSectionId.value = sectionId;
    }

    loading.value.posts = true;
    try {
      const newPosts = await forumApi.getForumPosts(
        teamId,
        sectionId,
        postPagination.value.page,
        postPagination.value.size
      );

      if (isLoadMore) {
        posts.value.push(...newPosts);
      } else {
        posts.value = newPosts;
      }

      // 判断是否还有更多 (如果返回数量小于 pageSize，说明到底了)
      if (newPosts.length < postPagination.value.size) {
        postPagination.value.hasMore = false;
      } else {
        postPagination.value.page += 1;
      }
    } finally {
      loading.value.posts = false;
    }
  }

  async function addPost(teamId: string, sectionId: string, data: ForumPostCreateRequest) {
    loading.value.action = true;
    try {
      const newPost = await forumApi.createForumPost(teamId, sectionId, data);
      // 如果当前就在这个版块，插入到最前面
      if (currentSectionId.value === sectionId) {
        posts.value.unshift(newPost);
      }
      return newPost;
    } finally {
      loading.value.action = false;
    }
  }

  async function fetchPostDetail(teamId: string, postId: string) {
    loading.value.detail = true;
    try {
      const post = await forumApi.getForumPostDetail(teamId, postId);
      currentPost.value = post;
      return post;
    } finally {
      loading.value.detail = false;
    }
  }

  async function editPost(teamId: string, postId: string, data: ForumPostModifyRequest) {
    loading.value.action = true;
    try {
      const updatedPost = await forumApi.updateForumPost(teamId, postId, data);

      // 更新详情
      if (currentPost.value?.id === postId) {
        currentPost.value = updatedPost;
      }
      // 更新列表
      const index = posts.value.findIndex(p => p.id === postId);
      if (index !== -1) {
        posts.value[index] = updatedPost;
      }
    } finally {
      loading.value.action = false;
    }
  }

  async function removePost(teamId: string, postId: string) {
    loading.value.action = true;
    try {
      await forumApi.deleteForumPost(teamId, postId);
      posts.value = posts.value.filter(p => p.id !== postId);
      if (currentPost.value?.id === postId) {
        currentPost.value = null;
      }
    } finally {
      loading.value.action = false;
    }
  }

  async function togglePostLike(teamId: string, post: ForumPost) {
    // 乐观更新 UI
    const originalStatus = post.liked_by_current_user;
    const originalCount = post.likes_count;

    // 先在本地修改状态
    const updateLocalState = (liked: boolean, count: number) => {
      post.liked_by_current_user = liked;
      post.likes_count = count;

      // 同步更新 currentPost
      if (currentPost.value?.id === post.id) {
        currentPost.value.liked_by_current_user = liked;
        currentPost.value.likes_count = count;
      }
    };

    if (originalStatus) {
      updateLocalState(false, originalCount - 1);
    } else {
      updateLocalState(true, originalCount + 1);
    }

    try {
      if (originalStatus) {
        await forumApi.unlikeForumPost(teamId, post.id);
      } else {
        await forumApi.likeForumPost(teamId, post.id);
      }
    } catch (error) {
      // 失败回滚
      updateLocalState(originalStatus, originalCount);
      console.error('Failed to toggle like', error);
    }
  }

  // ================= Actions: Comments =================

  async function fetchComments(teamId: string, postId: string) {
    loading.value.comments = true;
    try {
      const data = await forumApi.getForumComments(teamId, postId);
      comments.value = data;
    } finally {
      loading.value.comments = false;
    }
  }

  async function addComment(teamId: string, postId: string, content: string) {
    loading.value.action = true;
    try {
      const newComment = await forumApi.createForumComment(teamId, postId, {content});
      comments.value.push(newComment);

      // 更新帖子评论计数
      if (currentPost.value?.id === postId) {
        currentPost.value.comments_count += 1;
      }
      const listPost = posts.value.find(p => p.id === postId);
      if (listPost) listPost.comments_count += 1;

      return newComment;
    } finally {
      loading.value.action = false;
    }
  }

  async function removeComment(teamId: string, commentId: string) {
    loading.value.action = true;
    try {
      await forumApi.deleteForumComment(teamId, commentId);
      comments.value = comments.value.filter(c => c.id !== commentId);

      // 更新帖子评论计数
      if (currentPost.value) {
        currentPost.value.comments_count = Math.max(0, currentPost.value.comments_count - 1);
      }
      const listPost = posts.value.find(p => p.id === currentPost.value?.id);
      if (listPost) {
        listPost.comments_count = Math.max(0, listPost.comments_count - 1);
      }
    } finally {
      loading.value.action = false;
    }
  }

  const filteredPosts = computed(() => {
    if (!searchQuery.value.trim()) return posts.value;

    const query = searchQuery.value.toLowerCase();
    return posts.value.filter(post => {
      // 搜索权重：标题 > 内容 > 作者
      const inTitle = post.title.toLowerCase().includes(query);
      const inContent = post.content.toLowerCase().includes(query);
      const inAuthor = (post.author.nickname || post.author.username).toLowerCase().includes(query);

      return inTitle || inContent || inAuthor;
    });
  });

  return {
    // State
    sections,
    currentSectionId,
    posts,
    postPagination,
    currentPost,
    comments,
    loading,

    // Actions
    fetchSections,
    addSection,
    editSection,
    removeSection,

    fetchPosts,
    addPost,
    fetchPostDetail,
    editPost,
    removePost,
    togglePostLike,

    fetchComments,
    addComment,
    removeComment,

    searchQuery,    // 导出
    filteredPosts,
  };
});
