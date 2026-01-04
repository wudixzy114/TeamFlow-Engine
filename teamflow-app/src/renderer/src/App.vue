<template>
  <router-view/>
  <Toaster/>
</template>

<script lang="ts" setup>
import {useAiController} from './composables/useAiController';
import {Toaster} from "vue-sonner";
import 'vue-sonner/style.css'

useAiController();
</script>
