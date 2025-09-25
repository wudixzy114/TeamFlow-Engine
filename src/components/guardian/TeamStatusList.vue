<template>
  <el-card shadow="hover">
    <template #header>
      <div class="font-bold">团队成员</div>
    </template>
    <div class="space-y-3">
      <div v-for="member in teamMembers" :key="member.id" class="flex items-center justify-between">
        <span>{{ member.name }}</span>
        <div class="flex items-center space-x-2">
          <el-tag :type="member.status === 'Flowing' ? 'success' : 'info'" size="small">
            {{ member.status }}
          </el-tag>
          <el-button size="small" @click="contactMember(member)">联系 TA</el-button>
        </div>
      </div>
    </div>
  </el-card>

  <AsyncMessageComposer v-model="composerVisible" :target-user="selectedUser"/>
</template>

<script lang="ts" setup>
import {ref} from 'vue';
import AsyncMessageComposer from './AsyncMessageComposer.vue';
import {ElMessage} from "element-plus";

interface TeamMember {
  id: number;
  name: string;
  status: 'Available' | 'Flowing';
}

const composerVisible = ref(false);
const selectedUser = ref<TeamMember | null>(null);

const teamMembers = ref<TeamMember[]>([
  {id: 1, name: 'Alice', status: 'Available'},
  {id: 2, name: 'Bob', status: 'Flowing'},
  {id: 3, name: 'Charlie', status: 'Available'},
]);

const contactMember = (member: TeamMember) => {
  if (member.status === 'Flowing') {
    selectedUser.value = member;
    composerVisible.value = true;
  } else {
    ElMessage.info(`正在为你连接 ${member.name}... (正常沟通)`);
  }
};
</script>