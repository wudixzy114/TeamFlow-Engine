<script lang="ts" setup>
import {ref, computed, watch, onMounted} from 'vue';
import {TresCanvas, useTresContext} from '@tresjs/core';
import {OrbitControls, Line2} from '@tresjs/cientos';
import {EffectComposer, UnrealBloom} from '@tresjs/post-processing';
import * as THREE from 'three';
import gsap from 'gsap';
import {useSkillTreeStore} from '@/stores/skillTree';
import SkillNode3D from '@/components/skillTree/SkillNode3D.vue';
import SkillEnvironment from '@/components/skillTree/SkillEnvironment.vue';
import SkillNodeModal from '@/components/skillTree/SkillNodeModal.vue';
import ConfirmModal from '@/components/share/ConfirmModal.vue'; // 引入通用确认框
import {toast} from "vue-sonner";

const store = useSkillTreeStore();
const activeMode = ref<'me' | 'team'>('me');

const cameraRef = ref();
const controlsRef = ref();

// --- 删除确认框状态 ---
const confirmState = ref({
  isOpen: false,
  title: '',
  description: '',
  targetRawId: null as string | null
});

// 模态框与右键
const isModalOpen = ref(false);
const modalMode = ref<'add' | 'edit'>('add');
const contextMenuTarget = ref<any>(null); // 右键操作的目标
const contextMenu = ref({visible: false, x: 0, y: 0});

onMounted(() => {
  store.fetchGraph('me');
});

// 模式切换动画
watch(activeMode, (newMode) => {
  store.fetchGraph(newMode);
  if (cameraRef.value && controlsRef.value) {
    gsap.killTweensOf(controlsRef.value.target);
    gsap.killTweensOf(cameraRef.value.position);

    gsap.to(controlsRef.value.target, {x: 0, y: 0, z: 0, duration: 1.5, ease: 'power2.inOut'});
    gsap.to(cameraRef.value.position, {x: 0, y: 10, z: 60, duration: 1.5, ease: 'power2.inOut'});
  }
});

// 搜索监听：如果有搜索结果，自动聚焦第一个
watch(() => store.searchQuery, (newVal) => {
  if (newVal && store.highlightedNodeIds && store.highlightedNodeIds.size > 0) {
    const firstMatchId = Array.from(store.highlightedNodeIds)[0];
    const node = store.graphNodes.find(n => n.id === firstMatchId);
    if (node) focusOnNode(node);
  } else if (!newVal) {
    store.activeNodeId = null;
  }
});


// --- 辅助函数：根据截图结构精准提取 ---
function getRealControls(refValue: any) {
  if (!refValue) return null;

  // 🎯 命中截图中的结构：Proxy -> instance(Ref) -> value(OrbitControls)
  if (refValue.instance && refValue.instance.value && refValue.instance.value.target) {
    return refValue.instance.value;
  }

  // 备用：有时候是 Proxy -> value(OrbitControls)
  if (refValue.value && refValue.value.target) {
    return refValue.value;
  }

  // 备用：有时候直接是 OrbitControls
  if (refValue.target && typeof refValue.update === 'function') {
    return refValue;
  }

  return null;
}

function focusOnNode(node: any) {
  if (!node) return;

  // 1. 获取 Camera (通常 cameraRef.value 就是真身)
  const camera = cameraRef.value;

  // 2. 获取 Controls (使用上面的精准提取函数)
  const controls = getRealControls(controlsRef.value);

  // 🚨 调试日志：如果这次还不行，请把这个 log 截图给我
  if (!controls || !controls.target) {
    console.error("❌ 提取失败。结构路径尝试：controlsRef.value?.instance?.value", {
      原始对象: controlsRef.value,
      尝试instance: controlsRef.value?.instance,
      尝试instanceValue: controlsRef.value?.instance?.value
    });
    return;
  }

  // --- 3. 坐标清洗 ---
  const tx = Number(node.x || 0);
  const ty = Number(node.y || 0);
  const tz = Number(node.z || 0);
  const targetVec = new THREE.Vector3(tx, ty, tz);

  // --- 4. 计算新相机位置 ---
  const currentCamPos = camera.position.clone();

  // 保持当前视角方向，只拉近距离
  const offsetDir = new THREE.Vector3().subVectors(currentCamPos, targetVec);

  // 防止重合导致 NaN
  if (offsetDir.lengthSq() < 0.1 || isNaN(offsetDir.x)) {
    offsetDir.set(10, 10, 10);
  }

  // 设定观察距离为 25
  offsetDir.normalize().multiplyScalar(25);
  const newCamPos = targetVec.clone().add(offsetDir);

  // --- 5. 执行动画 ---
  // 此时 controls.target 绝对存在
  gsap.killTweensOf(controls.target);
  gsap.killTweensOf(camera.position);

  // 移动控制器中心
  gsap.to(controls.target, {
    x: tx,
    y: ty,
    z: tz,
    duration: 1.2,
    ease: "power3.inOut",
    onUpdate: () => {
      controls.update();
    }
  });

  // 移动相机
  gsap.to(camera.position, {
    x: newCamPos.x,
    y: newCamPos.y,
    z: newCamPos.z,
    duration: 1.2,
    ease: "power3.inOut"
  });
}

function onNodeClick(node: any) {
  store.activeNodeId = node.id;
  contextMenu.value.visible = false;
  focusOnNode(node);
}

// --- 右键菜单逻辑 ---
function onNodeRightClick(payload: { node: any; event: MouseEvent }) {
  if (activeMode.value === 'team') {
    toast.info('Team view is read-only');
    return;
  }
  contextMenuTarget.value = payload.node;
  // 直接使用原始鼠标事件（TresJS 会把原生 event 作为 event.originalEvent 或 event.nativeEvent）
  const mouseEvent = (payload.event as any).nativeEvent ||
    (payload.event as any).originalEvent ||
    payload.event as MouseEvent;

  if (mouseEvent && mouseEvent.clientX !== undefined) {
    contextMenu.value = {
      visible: true,
      x: mouseEvent.clientX,
      y: mouseEvent.clientY
    };
  } else {
    // 最终兜底：屏幕中心
    contextMenu.value = {
      visible: true,
      x: window.innerWidth / 2,
      y: window.innerHeight / 2
    };
  }
}

// Side Panel 操作
function openAddChild(node?: any) {
  contextMenuTarget.value = node || store.activeNodeData;
  modalMode.value = 'add';
  isModalOpen.value = true;
  contextMenu.value.visible = false;
}

function openEditNode(node?: any) {
  const target = node || store.activeNodeData;
  if (target?.type === 'ROOT') {
    toast.warning('Root node cannot be edited');
    return;
  }
  contextMenuTarget.value = target;
  modalMode.value = 'edit';
  isModalOpen.value = true;
  contextMenu.value.visible = false;
}

// 触发删除流程（打开确认框）
function handleDeleteTrigger(node?: any) {
  const target = node || store.activeNodeData;
  if (!target) return;

  if (target.type === 'ROOT') {
    toast.error('禁止摧毁系统核心 (ROOT Node Protected)');
    return;
  }

  confirmState.value = {
    isOpen: true,
    title: `分解节点: ${target.name}`,
    description: `确定要移除该节点吗？如果该节点包含子技能，它们也将失去连接。此操作不可逆。`,
    targetRawId: target.rawId
  };
  contextMenu.value.visible = false;
}

async function onConfirmDelete() {
  if (confirmState.value.targetRawId) {
    const success = await store.deleteNode(confirmState.value.targetRawId);
    if (success) {
      await store.fetchGraph(activeMode.value);
      store.activeNodeId = null;
    }
  }
  confirmState.value.isOpen = false;
}

async function handleModalConfirm(payload: any) {
  const target = contextMenuTarget.value;
  let success = false;

  if (modalMode.value === 'add') {
    const parentId = target ? target.rawId : null;
    success = await store.addNode(payload.name, parentId, payload.meta);
  } else if (target) {
    success = await store.updateNode(target.rawId, {
      new_name: payload.name,
      meta_data: payload.meta
    });
  }

  if (success) {
    await store.fetchGraph(activeMode.value);
    contextMenuTarget.value = null;
    isModalOpen.value = false;
  }
}

const activeNodeUI = computed(() => {
  const node = store.activeNodeData;
  if (!node) return null;

  switch (node.type) {
    case 'ROOT':
      return {
        themeClass: 'from-amber-500/20 to-transparent text-amber-400 border-amber-500/30',
        icon: 'i-carbon-cube',
        label: 'SYSTEM CORE',
        canEdit: false,
        canDelete: false,
        canAdd: true
      };
    case 'USER':
      return {
        themeClass: 'from-cyan-500/20 to-transparent text-cyan-400 border-cyan-500/30',
        icon: 'i-carbon-user-avatar-filled-alt',
        label: 'NEURAL LINK',
        canEdit: false, // 通常由系统管理
        canDelete: false,
        canAdd: true
      };
    case 'SKILL':
    default:
      return {
        themeClass: 'from-primary/20 to-transparent text-primary border-primary/30',
        icon: 'i-carbon-skill-level-advanced',
        label: 'ABILITY NODE',
        canEdit: true,
        canDelete: true,
        canAdd: true
      };
  }
});

// 连线数据：使用扁平数组格式（最新 @tresjs/cientos Line2 支持）
const linksData = computed(() => {
  if (!store.graphNodes || !store.graphLinks) return [];
  const nodeMap = new Map(store.graphNodes.map(n => [n.id, n]));

  const result: { id: string; points: number[]; isHighlighted: boolean; color: string }[] = [];

  for (const link of store.graphLinks) {
    const source = typeof link.source === 'object' ? link.source : nodeMap.get(link.source);
    const target = typeof link.target === 'object' ? link.target : nodeMap.get(link.target);

    if (!source || !target) continue;

    const isHighlighted = store.highlightedNodeIds
      ? (store.highlightedNodeIds.has(source.id) && store.highlightedNodeIds.has(target.id))
      : true;

    let linkColor;
    if (isHighlighted) {
      linkColor = getNodeColor(target); // 使用上面定义的动态取色函数
    } else {
      linkColor = '#1e293b'; // 暗淡的灰色
    }

    result.push({
      id: `${link.source}-${link.target}`,
      points: [source.x!, source.y!, source.z!, target.x!, target.y!, target.z!],
      isHighlighted,
      color: linkColor
    });
  }

  return result;
});

const NEON_PALETTE = [
  '#FF0055', // Neon Red
  '#00FF9F', // Neon Green
  '#00F3FF', // Cyan
  '#FFD700', // Gold
  '#BC13FE', // Electric Purple
  '#FF7700', // Safety Orange
  '#F0F',    // Magenta
  '#4D4DFF', // Neon Blue
];

function getNodeColor(node: any) {
  if (node.type === 'ROOT') return '#FFD700'; // Core Gold
  if (node.type === 'USER') return '#00F3FF'; // User Cyan

  // 对于普通技能，根据 ID 哈希取色
  let hash = 0;
  const str = node.id || node.name;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % NEON_PALETTE.length;
  return NEON_PALETTE[index];
}
</script>


<template>
  <div class="relative w-full h-full bg-[#050505] overflow-hidden font-sans">

    <!-- 1. Header / HUD -->
    <div
      class="absolute top-0 left-0 right-0 z-20 px-6 pb-6 pt-20 flex justify-between items-start pointer-events-none">
      <div class="pointer-events-auto flex flex-col gap-4">
        <div>
          <h1
            class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-white/20 tracking-tighter">
            NEXUS
          </h1>
          <div class="flex items-center gap-2 text-xs font-mono text-primary mt-1">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            {{ activeMode === 'me' ? 'SYSTEM: FOCUS' : 'SYSTEM: CONNECTION' }}
          </div>
        </div>

        <div class="glass-panel p-1 inline-flex rounded-lg">
          <button
            v-for="mode in ['me', 'team']" :key="mode"
            :class="activeMode === mode ? 'bg-white/10 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'"
            class="px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-all"
            @click="activeMode = mode as any"
          >
            {{ mode }}
          </button>
        </div>
      </div>

      <div class="pointer-events-auto w-80 relative group">
        <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <div class="i-carbon-search text-gray-500 group-focus-within:text-primary transition-colors"/>
        </div>
        <input
          v-model="store.searchQuery"
          class="w-full bg-black/40 backdrop-blur-md border border-white/10 rounded-full py-2.5 pl-10 pr-4 text-sm text-white focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--c-primary),0.2)] outline-none transition-all"
          placeholder="Search node or tag..."
          type="text"
        />
        <div v-if="store.searchQuery" class="absolute right-3 top-2.5 cursor-pointer text-gray-500 hover:text-white"
             @click="store.searchQuery = ''">
          <div class="i-carbon-close"/>
        </div>
      </div>
    </div>

    <!-- 2. Side Panel (根据节点类型动态渲染) -->
    <transition name="slide-right">
      <div v-if="store.activeNodeId && store.activeNodeData && activeNodeUI"
           class="absolute right-0 top-14 bottom-0 w-96 bg-card/90 backdrop-blur-2xl border-l border-white/5 z-20 shadow-2xl flex flex-col">

        <!-- Dynamic Header -->
        <div :class="activeNodeUI.themeClass" class="p-6 border-b bg-gradient-to-b">
          <div class="flex justify-between items-start mb-4">
            <div
              class="flex items-center gap-2 text-xs font-mono uppercase tracking-widest border border-current/30 px-2 py-0.5 rounded backdrop-blur-md bg-black/20">
              <div :class="activeNodeUI.icon" class="text-sm"></div>
              {{ activeNodeUI.label }}
            </div>
            <button class="text-white/50 hover:text-white transition" @click="store.activeNodeId = null">
              <div class="i-carbon-close text-xl"/>
            </button>
          </div>
          <h2 class="text-3xl font-bold text-white leading-tight mb-2 drop-shadow-md">
            {{ store.activeNodeData.name }}
          </h2>

          <!-- ROOT 不显示熟练度 -->
          <div v-if="store.activeNodeData.type !== 'ROOT'" class="mt-4">
            <div class="flex justify-between text-xs text-white/60 mb-1">
              <span>{{ store.activeNodeData.type === 'USER' ? 'Sync Rate' : 'Proficiency' }}</span>
              <span>{{ store.activeNodeData.meta_data?.proficiency || 0 }}%</span>
            </div>
            <div class="h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
              <div
                :style="{ width: `${store.activeNodeData.meta_data?.proficiency || 0}%` }"
                class="h-full bg-current shadow-[0_0_10px_currentColor]"
              ></div>
            </div>
          </div>
        </div>

        <!-- Panel Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">

          <!-- ROOT Special Message -->
          <div v-if="store.activeNodeData.type === 'ROOT'"
               class="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
            <h4 class="text-amber-400 font-bold text-sm mb-2 flex items-center gap-2">
              <div class="i-carbon-information-filled"></div>
              SYSTEM STATUS
            </h4>
            <p class="text-amber-200/70 text-sm">
              Current Neural Nexus Core is online. All subordinate nodes are functioning within expected parameters.
            </p>
          </div>

          <!-- Description -->
          <div v-if="store.activeNodeData.meta_data?.description"
               class="bg-white/5 rounded-xl p-4 border border-white/5">
            <h4 class="text-xs font-bold text-gray-500 uppercase mb-2">Description</h4>
            <p class="text-sm text-gray-300 leading-relaxed">{{ store.activeNodeData.meta_data.description }}</p>
          </div>

          <!-- Tags -->
          <div v-if="store.activeNodeData.meta_data?.tags?.length">
            <h4 class="text-xs font-bold text-gray-500 uppercase mb-2">Tags</h4>
            <div class="flex flex-wrap gap-2">
               <span v-for="tag in store.activeNodeData.meta_data.tags" :key="tag"
                     class="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-xs text-gray-300">
                 #{{ tag }}
               </span>
            </div>
          </div>

          <!-- Info Grid -->
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-surface/50 p-3 rounded-lg border border-white/5">
              <div class="text-xs text-gray-500">Status</div>
              <div class="text-sm font-medium text-white capitalize mt-1 flex items-center gap-2">
                <span :class="store.activeNodeData.type === 'ROOT' ? 'bg-amber-500' : 'bg-green-500'"
                      class="w-2 h-2 rounded-full"></span>
                {{ store.activeNodeData.meta_data?.status || 'Active' }}
              </div>
            </div>
            <div class="bg-surface/50 p-3 rounded-lg border border-white/5">
              <div class="text-xs text-gray-500">Links</div>
              <div class="text-sm font-medium text-white mt-1">{{ linksData.filter(l => l.isHighlighted).length }}
                Nodes
              </div>
            </div>
          </div>
        </div>

        <!-- Panel Footer (Actions) -->
        <div v-if="activeMode === 'me'" class="p-6 border-t border-white/5 bg-black/20">
          <div :class="activeNodeUI.canDelete ? 'grid-cols-2' : 'grid-cols-1'" class="grid gap-3">

            <!-- Add Child (Everyone can usually add child) -->
            <button v-if="activeNodeUI.canAdd" class="btn-primary w-full justify-center" @click="openAddChild()">
              <div class="i-carbon-add-alt"/>
              Extend
            </button>

            <!-- Edit (Root/User cannot edit) -->
            <button v-if="activeNodeUI.canEdit" class="btn-outline w-full justify-center" @click="openEditNode()">
              <div class="i-carbon-settings"/>
              Config
            </button>
          </div>

          <!-- Delete (Protected) -->
          <button v-if="activeNodeUI.canDelete"
                  class="w-full mt-3 btn-ghost text-red-400 hover:text-red-300 hover:bg-red-500/10 justify-center"
                  @click="handleDeleteTrigger()">
            <div class="i-carbon-trash-can mr-2"/>
            Disintegrate Node
          </button>

          <div v-if="!activeNodeUI.canDelete" class="w-full mt-3 text-center text-xs text-gray-600 font-mono">
            [ LOCKED PROTECTION ]
          </div>
        </div>
      </div>
    </transition>

    <!-- 3. 3D Canvas -->
    <TresCanvas
      :dpr="1.5"
      clear-color="#050505"
      power-preference="high-performance"
      shadows
    >
      <TresPerspectiveCamera ref="cameraRef" :fov="45" :position="[0, 10, 60]" make-default/>

      <OrbitControls
        ref="controlsRef"
        :damping-factor="0.05"
        :enable-damping="true"
        make-default
      />

      <EffectComposer>
        <UnrealBloom :intensity="1.2" :luminance-threshold="0.1" :radius="0.6" :strength="0.8"/>
      </EffectComposer>

      <SkillEnvironment/>

      <TresGroup>
        <SkillNode3D
          v-for="node in store.graphNodes"
          :key="node.id"
          :is-highlighted="!store.highlightedNodeIds || store.highlightedNodeIds.has(node.id)"
          :is-selected="store.activeNodeId === node.id"
          :node="node"
          @click="onNodeClick"
          @right-click="onNodeRightClick"
        />

        <Line2
          v-for="(link, idx) in linksData"
          :key="idx"
          :color="link.color"
          :depth-test="false"
          :line-width="link.isHighlighted ? 2.5 : 1"
          :opacity="link.isHighlighted ? 0.8 : 0.05"
          :points="link.points"
          :render-order="-1"
          :transparent="true"
        />
      </TresGroup>
    </TresCanvas>

    <!-- Context Menu -->
    <div
      v-if="contextMenu.visible"
      :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
      class="fixed z-50 glass-panel rounded-lg overflow-hidden min-w-40 py-1 border border-white/10 shadow-xl"
      @click.stop
    >
      <button class="w-full text-left px-4 py-2 hover:bg-white/10 text-sm text-gray-200 flex items-center gap-2"
              @click="openAddChild(contextMenuTarget)">
        <div class="i-carbon-add-alt"/>
        Branch Out
      </button>

      <!-- 只在非根节点显示编辑和删除 -->
      <template v-if="contextMenuTarget && contextMenuTarget.type !== 'ROOT' && contextMenuTarget.type !== 'USER'">
        <button class="w-full text-left px-4 py-2 hover:bg-white/10 text-sm text-gray-200 flex items-center gap-2"
                @click="openEditNode(contextMenuTarget)">
          <div class="i-carbon-settings"/>
          Configure
        </button>
        <div class="h-px bg-white/10 my-1"></div>
        <button class="w-full text-left px-4 py-2 hover:bg-red-500/20 text-sm text-red-400 flex items-center gap-2"
                @click="handleDeleteTrigger(contextMenuTarget)">
          <div class="i-carbon-trash-can"/>
          Disintegrate
        </button>
      </template>
    </div>

    <!-- Modals -->
    <SkillNodeModal
      :initial-data="modalMode === 'edit' ? contextMenuTarget : undefined"
      :is-edit="modalMode === 'edit'"
      :is-open="isModalOpen"
      @close="isModalOpen = false"
      @confirm="handleModalConfirm"
    />

    <!-- 集成通用确认框 -->
    <ConfirmModal
      :description="confirmState.description"
      :is-open="confirmState.isOpen"
      :title="confirmState.title"
      cancel-text="取消操作"
      confirm-text="确认销毁"
      @close="confirmState.isOpen = false"
      @confirm="onConfirmDelete"
    />

    <div v-if="contextMenu.visible" class="fixed inset-0 z-40" @click="contextMenu.visible = false"/>
  </div>
</template>

<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
}
</style>
