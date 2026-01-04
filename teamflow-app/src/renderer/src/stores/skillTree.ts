import {defineStore} from 'pinia';
import {ref} from 'vue';
import {
  getSkillTree,
  getTeamSkillTree,
  addRootSkillNode,
  addChildSkillNode,
  updateSkillNode as apiUpdateSkillNode,
  deleteSkillNode as apiDeleteSkillNode
} from '@/api/skillTree';
import {useTeamsStore} from '@/stores/teams';
import {toast} from 'vue-sonner';
import * as d3 from 'd3-force-3d';

// 3D 节点接口
export interface GraphNode {
  id: string;
  name: string;
  type: 'ROOT' | 'USER' | 'SKILL';
  val: number; // 大小/权重
  color?: string;
  x?: number;
  y?: number;
  z?: number;
  meta_data?: any;
  // 原始数据引用，用于后续操作
  rawId?: string;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  distance?: number;
}

export const useSkillTreeStore = defineStore('skillTree', () => {
  // State
  const graphNodes = ref<GraphNode[]>([]);
  const graphLinks = ref<GraphLink[]>([]);
  const isLoading = ref(false);
  const activeNodeId = ref<string | null>(null); // 当前选中的焦点节点

  const searchQuery = ref('');

  // Layout Engine
  let simulation: any = null;

  // Getters

  // 计算需要高亮的节点 ID 集合 (包括选中的节点、其父节点、其子节点)
  const highlightedNodeIds = computed(() => {
    const ids = new Set<string>();

    // 1. 如果有搜索词，高亮匹配项
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase();
      graphNodes.value.forEach(n => {
        if (n.name.toLowerCase().includes(query) ||
          (n.meta_data?.tags && n.meta_data.tags.some((t: string) => t.toLowerCase().includes(query)))) {
          ids.add(n.id);
        }
      });
      return ids; // 搜索模式下只显示搜索结果
    }

    // 2. 如果没有选中节点，全部高亮 (即不暗化任何节点)
    if (!activeNodeId.value) return null;

    // 3. 选中模式：高亮当前节点 + 邻居
    ids.add(activeNodeId.value);

    // 查找直接连接的邻居
    graphLinks.value.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;

      if (sourceId === activeNodeId.value) ids.add(targetId);
      if (targetId === activeNodeId.value) ids.add(sourceId);
    });

    return ids;
  });

  const activeNodeData = computed(() =>
    graphNodes.value.find(n => n.id === activeNodeId.value)
  );

  // Actions

  /**
   * 将树形数据扁平化为图结构
   * 核心逻辑：团队视图下，合并同名技能以显示 Connection
   */
  function processDataToGraph(treeData: any, mode: 'me' | 'team') {
    const nodes: Map<string, GraphNode> = new Map();
    const links: GraphLink[] = [];

    function traverse(node: any, parentId: string | null, depth: number) {
      // 生成唯一ID：
      // 个人模式：直接用 node.id
      // 团队模式：如果是技能，使用 name 作为 ID 来实现合并效果；如果是人，使用 node.id
      let uniqueId = node.id || `temp-${node.name}`;

      // 团队模式下的技能合并逻辑 (Connection Story)
      if (mode === 'team' && node.type !== 'USER' && depth > 0) {
        // 使用名称作为唯一标识，这样不同人的相同技能会合并为一个节点
        uniqueId = `skill-${node.name.toLowerCase()}`;
      }

      let type: 'ROOT' | 'USER' | 'SKILL' = 'SKILL';
      if (depth === 0) type = 'ROOT';
      else if (mode === 'team' && depth === 1) type = 'USER'; // 团队模式下，第一层子节点是人

      // 如果节点不存在，创建它
      if (!nodes.has(uniqueId)) {
        nodes.set(uniqueId, {
          id: uniqueId,
          rawId: node.id, // 真实操作用的ID
          name: node.name,
          type: type,
          val: type === 'ROOT' ? 20 : (type === 'USER' ? 12 : Math.max(2, 8 - depth)), // 深度越深，节点越小
          meta_data: node.meta_data || {},
          // 初始随机位置，防止重叠
          x: Math.random() * 10,
          y: Math.random() * 10,
          z: Math.random() * 10
        });
      }

      // 创建连接
      if (parentId) {
        // 防止重复连接
        const linkExists = links.some(l =>
          (l.source === parentId && l.target === uniqueId) ||
          (l.source === uniqueId && l.target === parentId)
        );

        if (!linkExists) {
          links.push({source: parentId, target: uniqueId});
        }
      }

      if (node.children) {
        node.children.forEach((child: any) => traverse(child, uniqueId, depth + 1));
      }
    }

    if (treeData) {
      traverse(treeData, null, 0);
    }

    return {nodes: Array.from(nodes.values()), links};
  }

  /**
   * 运行 3D 力导向布局计算位置
   */
  function computeLayout() {
    if (simulation) simulation.stop();

    simulation = d3.forceSimulation(graphNodes.value, 3)
      .force('link', d3.forceLink(graphLinks.value).id((d: any) => d.id).distance((d: any) => {
        // 根节点连接长一些，技能密集一些
        if (d.source.type === 'ROOT' || d.target.type === 'ROOT') return 40;
        return 20;
      }))
      .force('charge', d3.forceManyBody().strength(-200)) // 增强排斥
      .force('center', d3.forceCenter(0, 0, 0))
      .force('collide', d3.forceCollide((d: any) => d.val * 1.5).iterations(2))
      .force('y', d3.forceY(0).strength(0.05)); // 稍微压扁一点 Y 轴，让结构更横向展开

    simulation.tick(120);
    simulation.stop();
  }

  async function fetchGraph(mode: 'me' | 'team') {
    isLoading.value = true;
    activeNodeId.value = null; // 重置选中
    try {
      let data;
      if (mode === 'me') {
        data = await getSkillTree();
      } else {
        const teamStore = useTeamsStore();
        if (!teamStore.currentTeamId) throw new Error("No Team Selected");
        data = await getTeamSkillTree(teamStore.currentTeamId);
      }

      const {nodes, links} = processDataToGraph(data, mode);

      // 保持旧节点的位置以实现平滑过渡 (可选优化)
      graphNodes.value = nodes;
      graphLinks.value = links;

      computeLayout();

    } catch (e) {
      console.error(e);
      toast.error('Failed to load skill universe');
    } finally {
      isLoading.value = false;
    }
  }

  // --- CRUD Actions (Proxy to API) ---

  async function addNode(name: string, parentRawId: string | null, meta: any) {
    try {
      if (parentRawId) {
        await addChildSkillNode(parentRawId, {name, meta_data: meta});
      } else {
        await addRootSkillNode({name, meta_data: meta});
      }
      toast.success('Skill node materialized');
      // 重新获取以刷新图谱
      // 注意：这里简单处理，实际可优化为局部更新图数据
      return true;
    } catch (e) {
      toast.error('Failed to spawn node');
      return false;
    }
  }

  async function updateNode(nodeRawId: string, changes: any) {
    const node = graphNodes.value.find(n => n.rawId === nodeRawId);
    if (node?.type === 'ROOT') {
      toast.warning('核心节点不可修改 (ROOT Node is protected)');
      return false;
    }

    try {
      await apiUpdateSkillNode(nodeRawId, changes);
      toast.success('Node reconfiguration complete');
      return true;
    } catch (e) {
      toast.error('Update failed');
      return false;
    }
  }

  async function deleteNode(nodeRawId: string) {
    const node = graphNodes.value.find(n => n.rawId === nodeRawId);

    // 1. 根节点保护
    if (node?.type === 'ROOT') {
      toast.error('禁止摧毁系统核心 (ROOT Node cannot be destroyed)');
      return false;
    }

    try {
      await apiDeleteSkillNode(nodeRawId);
      toast.success('Node disintegrated');
      return true;
    } catch (e) {
      toast.error('Deletion failed');
      return false;
    }
  }

  return {
    graphNodes,
    graphLinks,
    isLoading,
    activeNodeId,
    activeNodeData,
    searchQuery,
    highlightedNodeIds,
    fetchGraph,
    addNode,
    updateNode,
    deleteNode
  };
});
