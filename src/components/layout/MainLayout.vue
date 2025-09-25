<template>
  <div class="common-layout bg-gray-100 min-h-screen">
    <el-container>
      <el-aside class="bg-white shadow-md" width="200px">
        <div class="p-4 text-center font-bold text-lg text-primary">
          TeamFlow Engine
        </div>
        <el-menu default-active="/dashboard" router>
          <el-menu-item index="/dashboard">
            <el-icon>
              <DataBoard/>
            </el-icon>
            <span>团队仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/achievements">
            <el-icon>
              <Trophy/>
            </el-icon>
            <span>成就与成长</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container direction="vertical">
        <el-header class="flex justify-between items-center bg-white border-b">
          <span class="text-gray-500">让心流成为常态</span>
          <FlowModeToggle/>
        </el-header>
        <el-main class="p-6">
          <router-view/>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script lang="ts" setup>
import {DataBoard, Trophy} from "@element-plus/icons-vue";
import FlowModeToggle from '@/components/guardian/FlowModeToggle.vue';
// 这里可以写布局相关的逻辑
</script>