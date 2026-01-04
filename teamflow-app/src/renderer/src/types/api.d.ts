export {};

declare global {
  // ==========================================
  // 1. 用户与认证 (Authentication & User)
  // ==========================================

  interface User {
    id: string; // uuid
    username: string;
    email: string; // format: email
    gender: string;
    profession: string;
    nickname: string;
    age: string;
  }

  // 登录与注册
  interface LoginRequest {
    email: string;
    password: string;
  }

  interface RegisterRequest {
    username: string;
    email: string;
    password: string;
  }

  interface TokenPair {
    refresh: string;
    access: string;
  }

  interface AccessToken {
    access: string;
  }

  interface RefreshTokenRequest {
    refresh: string;
  }

  // 密码与邮箱验证
  interface ForgotPasswordRequest {
    email: string;
  }

  interface ResetPasswordRequest {
    email: string;
    code: string;
    new_password: string;
  }

  interface EmailVerificationRequest {
    email: string;
    code: string;
  }

  // 个人信息修改
  // Schema: modifyUserInfo (fields are nullable)
  interface ModifyUserInfoRequest {
    username?: string | null;
    nickname?: string | null;
    age?: string | null;
    gender?: string | null;
    profession?: string | null;
  }

  interface ResetEmailRequest {
    new_email: string; // Query parameter in API
  }

  // ==========================================
  // 2. 团队管理 (Teams)
  // ==========================================

  interface Team {
    id: string; // uuid
    name: string;
    owner: User;
  }

  interface TeamCreate {
    name: string;
  }

  // 修改群组名
  interface TeamNameUpdateRequest {
    name: string;
  }

  // 更换群主
  interface TeamOwnerUpdateRequest {
    id: string; // user_id
  }

  // 获取成员列表响应
  interface TeamMembersResponse {
    owner: User;
    members: User[];
  }

  // 邀请相关
  // Schema: InviteInfo
  interface InvitationRecord {
    team_id: string;
    team_name: string;
    invite_code: string;
    status: string; // e.g., "pending"
    created_at: string; // date-time
    inviter_username: string;
  }

  // 发送邀请
  // Schema: EmailORUsername
  interface InvitationCreateRequest {
    email_username: string;
  }

  // 接受/拒绝邀请
  // Schema: InviteCode
  interface InvitationCode {
    code: string;
  }

  // 踢人
  interface KickMemberRequest {
    id: string; // member id
  }

  interface TeamDetail extends Team {
    members: User[];
  }

  // ==========================================
  // 3. 签到 (Check-ins)
  // ==========================================

  interface Checkin {
    id: string; // uuid
    user: User;
    created_at: string; // date-time
    challenge_level: number; // float
    skill_level: number; // float
    achievement_text?: string;
    obstacle_text?: string;
  }

  interface CheckinCreate {
    challenge_level: number; // float, -1 to 1
    skill_level: number; // float, -1 to 1
    achievement_text?: string | null;
    obstacle_text?: string | null;
  }

  interface CheckinTodayStatus {
    has_checked_in: boolean;
  }

  // ==========================================
  // 4. 数据看板 (Dashboard)
  // ==========================================

  // 情绪罗盘
  interface CompassTrendPoint {
    date: string; // format: date
    avg_challenge: number;
    avg_skill: number;
  }

  interface CompassData {
    period: string;
    trend_data: CompassTrendPoint[];
    distribution: {
      [key: string]: number; // e.g., "Flow": 10
    };
  }

  // 专注时长
  interface FocusTimeDailyTrend {
    date: string; // format: date
    hours: number;
  }

  interface FocusTimeData {
    period: string;
    total_hours: number;
    daily_trend: FocusTimeDailyTrend[];
  }

  // AI 洞察
  interface WordCloudItem {
    name: string;
    value: number;
  }

  interface AIInsights {
    boosters_wordcloud: WordCloudItem[];
    blockers_wordcloud: WordCloudItem[];
  }

  // ==========================================
  // 5. 高光时刻 (Recognition / Highlights)
  // ==========================================

  // 获取列表时的单项结构
  interface HighlightSingle {
    id: string; // uuid
    user: User;
    content: string;
    created_at: string; // date-time
    likes_count: number;
    liked_by_current_user: boolean; // 修正: API 返回的是这个字段，而不是 is_liked_by_me
  }

  // 发布高光
  interface HighlightCreate {
    content: string;
  }

  // 修改高光
  interface HighlightUpdate {
    id: string;
    content: string;
  }

  // 删除高光
  // Schema: HighlightId
  interface HighlightDelete {
    id: string;
  }

  interface Comment {
    id: string;
    user_id: string;
    highlight_id: string;
    content: string;
    created_at: string; // date-time
  }

  interface CommentContentRequest {
    content: string;
  }

  interface CommentModifyRequest extends CommentContentRequest {
    id: string
  }

  interface CommentDeleteRequest {
    id: string; // Comment id
  }

  // Kudos 能量卡
  interface Kudos {
    id: string; // uuid
    sender: User;
    receiver: User;
    card_type: string;
    message: string;
    created_at: string; // date-time
  }

  interface KudosCreate {
    receiver_id: string; // uuid
    card_type: string;
    message: string;
  }

  // ==========================================
  // 6. 心流仪式 (Flow Ritual)
  // ==========================================

  // 读取记录 (Schema: ReturnFlowSession)
  interface FlowSession {
    id: string;
    start_time: string;
    duration_minutes: number;
    task_description: string;
  }

  // 创建记录
  interface FlowSessionCreate {
    start_time: string; // date-time
    duration_minutes: number;
    task_description: string;
  }

  // 修改记录 (Schema: SessionModify)
  interface FlowSessionModify {
    id: string;
    task_description: string;
  }

  // 删除记录 (Schema: Sessionflow_id)
  interface FlowSessionDelete {
    id: string;
  }

  interface DateQuery {
    date: string; // format: date
  }

  // ==========================================
  // 7. 文化与成长 (Culture & Growth) & 消息
  // ==========================================

  // 团队公约
  interface Charter {
    content: string; // Markdown
    last_updated_by?: User;
    updated_at?: string; // date-time
  }

  interface CharterUpdate {
    content: string;
  }

  // --- 技能树相关 (Skill Tree) ---

  /** 技能树节点结构 */
  interface SkillTreeNode {
    id: string;
    name: string;
    /** 节点类型，例如 "USER" 或 "SKILL" */
    type?: string;
    children?: SkillTreeNode[];
    meta_data?: Record<string, any>;
  }

  /** 获取技能树的响应数据 */
  interface SkillTreeData {
    name: string;
    children: SkillTreeNode[];
  }

  /**
   * 创建技能节点请求体 (UserSkillItem)
   * 用于添加根节点或子节点
   */
  interface UserSkillItemRequest {
    name: string;
    meta_data?: Record<string, any>;
  }

  /** 创建节点成功的响应 */
  interface AddSkillNodeResponse {
    message: string;
    node_id: string;
  }

  /**
   * 修改技能节点请求体 (UserSkillModify)
   */
  interface ModifyNodeRequest {
    new_name?: string | null;
    meta_data?: Record<string, any> | null;
  }

  // 周报
  interface WeeklyDigestData {
    week_range: {
      start: string; // date
      end: string; // date
    };
    mindset_trend: CompassData;
    total_focus_hours: number;
    top_booster: string;
    top_blocker: string;
    kudos_received: number;
  }

  // 消息通知 (Message)
  interface Message {
    id: string;
    content: string;
    created_at: string; // date-time
    team_id?: string | null;
  }

  interface TeamMessage {
    content: string;
    created_at: Date;
    id: string;
    tag: string;
    team_id: string;
  }

  interface MessageDelete {
    message_id: string;
  }

  // 聊天室相关
  interface TeamChat {
    id: string;
    team_id: string;
    sender_id: string;
    content: string;
    tag: 'text' | 'file' | 'image' | string;
    created_at: string; // date-time
  }

  interface NewTeamChatRequest {
    content: string;
    tag: string;
  }

  interface DeleteTeamChatRequest {
    id: string;
  }

  interface NewTeamChatID {
    id: string;
  }

  export interface FileUploadRequest {
    tag: string;
    file: File;
  }

  export interface SendMessageResponse {
    message: string; // "success" or similar
  }

  // ==========================================
  // 8. 通用响应 (Common Responses)
  // ==========================================

  interface SuccessMessage {
    message: string;
  }

  interface ErrorResponse {
    detail: string;
  }

  // ==========================================
  // 9. 论坛 (Forum)
  // ==========================================

  interface ForumSection {
    id: string;
    team_id: string;
    name: string;
    description: string;
    created_at: string; // date-time
  }

  interface ForumSectionCreateRequest {
    name: string;
    description?: string;
  }

  interface ForumSectionModifyRequest {
    name?: string;
    description?: string;
  }

  interface ForumPost {
    id: string;
    section_id: string;
    title: string;
    content: string;
    author: User;
    created_at: string; // date-time
    updated_at: string; // date-time
    likes_count: number;
    comments_count: number;
    liked_by_current_user: boolean;
  }

  interface ForumPostCreateRequest {
    title: string;
    content: string;
  }

  interface ForumPostModifyRequest {
    title?: string;
    content?: string;
  }

  interface ForumComment {
    id: string;
    post_id: string;
    user: User;
    content: string;
    created_at: string; // date-time
  }

  interface ForumCommentCreateRequest {
    content: string;
  }
}
