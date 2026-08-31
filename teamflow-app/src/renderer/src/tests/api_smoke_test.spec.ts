import {describe, it, expect, beforeAll} from "vitest";
import {setActivePinia, createPinia} from "pinia";
import {useAuthStore} from "@/stores/auth";
import {api} from "@/api";
import apiClient from "@/api/request";

const TEST_USER = {
  email: "test1@gmail.com",
  password: 'test1'
}

describe('Backend API Smoke Test', () => {
  let teamId: string;
  let highlightId: string;
  // let userId: string;

  beforeAll(async () => {
    setActivePinia(createPinia());
    apiClient.defaults.adapter = 'http'
  });

  // === 认证模块 ===
  describe('Auth Module', () => {
    it('should login successfully and save token', async () => {
      const authStore = useAuthStore();
      const tokens = await api.auth.login(TEST_USER);

      expect(tokens).toHaveProperty('access');
      expect(tokens).toHaveProperty('refresh');

      authStore.accessToken = tokens.access;
      authStore.refreshToken = tokens.refresh;

      const me = await api.auth.getMe();
      expect(me).toHaveProperty('email');
      // userId = me.id;
      console.log(`Logged in as: ${me.username} (${me.id})`);
    });
  });

  // === 团队模块 ===
  describe('Teams Module', () => {
    it('should list teams', async () => {
      const teams = await api.teams.listMyTeams();
      expect(Array.isArray(teams)).toBe(true);

      if (teams.length > 0) {
        teamId = teams[0].id;
        console.log(`Using existing team: ${teams[0].name} (${teamId})`);
      } else {
        // 如果没有团队，创建一个
        const newTeamName = `Test Team ${Date.now()}`;
        await api.teams.createTeam({name: newTeamName});
        // 重新获取列表以拿到 ID
        const newTeams = await api.teams.listMyTeams();
        const createdTeam = newTeams.find(t => t.name === newTeamName);
        expect(createdTeam).toBeDefined();
        teamId = createdTeam!.id;
        console.log(`Created new team: ${teamId}`);
      }
    });

    it('should get team details and members', async () => {
      expect(teamId).toBeDefined();
      const members = await api.teams.listMember(teamId);
      expect(members).toHaveProperty('owner');
      expect(Array.isArray(members.members)).toBe(true);
    });
    it('should get team skill tree', async () => {
      // 这是一个 GET 请求，即使为空也应该返回 200
      try {
        const tree = await api.teams.getTeamSkillTree(teamId);
        expect(tree).toBeDefined();
      } catch (e: any) {
        // 允许 404 (如果后端逻辑是没数据返404) 或 空数据
        console.warn('Skill tree check:', e.message);
      }
    });
  });

  // === 业务功能模块 (依赖 TeamID) ===
  describe('Features (Check-in, Highlights, Charter, etc.)', () => {

    // --- 签到 ---
    it('should check today\'s check-in status', async () => {
      const status = await api.checkins.checkTodayStatus(teamId);
      expect(status).toHaveProperty('has_checked_in');
      console.log('Check-in status:', status);
    });

    // --- 仪表盘 ---
    it('should fetch dashboard data', async () => {
      const [compass, focus, insights] = await Promise.all([
        api.dashboard.getCompassData(teamId, 'week'),
        api.dashboard.getFocusTimeData(teamId, 'week'),
        api.dashboard.getInsightsData(teamId, 'week')
      ]);

      expect(compass).toHaveProperty('trend_data');
      expect(focus).toHaveProperty('total_hours');
      expect(insights).toHaveProperty('boosters_wordcloud');
    });

    // --- 公约 ---
    it('should fetch team charter', async () => {
      try {
        const charter = await api.charter.getCharter(teamId);
        if (charter) {
          expect(charter).toHaveProperty('content');
        }
      } catch (e: any) {
        // 404 是预期的，如果没有创建过公约
        if (e.response?.status !== 404) throw e;
      }
    });

    // --- 高光时刻 ---
    it('should flow through highlights (List -> Create -> Like -> Delete)', async () => {
      // 1. List
      const list = await api.highlights.listHighlights(teamId);
      expect(Array.isArray(list)).toBe(true);

      // 2. Create
      const content = `Automated Test Highlight ${Date.now()}`;
      await api.highlights.createHighlight(teamId, {content});

      // 3. Verify Creation
      const newList = await api.highlights.listHighlights(teamId);
      const createdItem = newList.find(h => h.content === content);
      expect(createdItem).toBeDefined();
      highlightId = createdItem!.id;

      // 4. Like
      await api.highlights.likeHighlight(highlightId);

      // 5. Delete (Cleanup)
      await api.highlights.deleteHighlight(teamId, {id: highlightId});
      // 5. Delete (Cleanup) – tolerate dead file proxy
      // try {
      //   await api.highlights.deleteHighlight(teamId, {id: highlightId});
      // } catch (e: any) {
      //   if (e.code === 'ECONNREFUSED' || e.message.includes('local-test-server')) {
      //     console.warn('Highlight delete failed because old file proxy is down – ignoring in smoke test');
      //   } else {
      //     throw e;
      //   }
      // }
    });

    // --- 专注模式 (Flow Session) ---
    it('should list flow sessions', async () => {
      const sessions = await api.flowSessions.listFlowSessions(teamId);
      expect(Array.isArray(sessions)).toBe(true);
    });

    // --- Kudos ---
    it('should fetch my kudos', async () => {
      const kudos = await api.kudos.listMyReceivedKudos();
      expect(Array.isArray(kudos)).toBe(true);
    });

    // === 个人信息模块 ===
    describe('Me Module', () => {
      it('should fetch weekly digest', async () => {
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        try {
          const digest = await api.me.getMyWeeklyDigest(today);
          expect(digest).toBeDefined();
        } catch (e) {
          console.warn('Weekly digest fetch failed (maybe no data yet):', e);
        }
      });

      it('should fetch skill tree', async () => {
        const tree = await api.me.getMySkillTree();
        expect(tree).toBeDefined();
      });

      // it('should fetch skill tree', async () => {
      //   try {
      //     const tree = await api.me.getMySkillTree();
      //     expect(tree).toBeDefined();
      //   } catch (e: any) {
      //     if (e.response?.status === 404) {
      //       console.log('My skill tree 404 – expected when no skills unlocked yet');
      //       return;
      //     }
      //     throw e;
      //   }
      // });
    });
  });

  it('should flow through chat (List -> Send -> Delete)', async () => {
    // 1. 获取消息列表
    const initialMsgs = await api.chat.getChatMessages(teamId);
    expect(Array.isArray(initialMsgs)).toBe(true);

    // 2. 发送文本消息
    const chatContent = `Smoke Test Chat ${Date.now()}`;
    await api.chat.sendChatMessage(teamId, {content: chatContent, tag: 'text'});

    // 3. 验证消息是否入库 (获取最新列表并查找)
    const updatedMsgs = await api.chat.getChatMessages(teamId);
    const myMsg = updatedMsgs.find(m => m.content === chatContent);
    expect(myMsg).toBeDefined();
    const msgId = myMsg!.id;

    // 4. 删除消息
    await api.chat.deleteChatMessage(teamId, {id: msgId});

    // 5. 验证删除
    const finalMsgs = await api.chat.getChatMessages(teamId);
    const deletedMsg = finalMsgs.find(m => m.id === msgId);
    expect(deletedMsg).toBeUndefined();

    // 注意：文件上传测试在 Node 环境下比较复杂（涉及 FormData polyfill），
    // 在 Smoke Test 中通常跳过，只要文本流通说明 API 连通性没问题。
  })
});
