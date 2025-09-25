<template>
  <el-dialog
      :model-value="modelValue"
      :title="`联系 ${targetUser?.name} (专注中)`"
      width="500px"
      @update:modelValue="$emit('update:modelValue', $event)"
  >
    <p class="text-sm text-gray-500 mb-4">
      你的消息将由 AI 助理处理并结构化，在 {{ targetUser?.name }} 退出专注后以摘要形式发送，请放心。
    </p>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="你的消息" prop="message">
        <el-input v-model="form.message" :rows="4" type="textarea"/>
      </el-form-item>
      <el-form-item label="紧急程度" prop="urgency">
        <el-radio-group v-model="form.urgency">
          <el-radio-button label="low">低</el-radio-button>
          <el-radio-button label="medium">中</el-radio-button>
          <el-radio-button label="high">高 (会立即通知)</el-radio-button>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="submitForm">发送给 AI 助理</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import {ref, reactive} from 'vue';
import {ElMessage, type FormInstance, type FormRules} from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  targetUser: { name: string } | null;
}>();

const emit = defineEmits(['update:modelValue']);

const formRef = ref<FormInstance>();
const form = reactive({
  message: '',
  urgency: 'low',
});

const rules = reactive<FormRules>({
  message: [{required: true, message: '请输入消息内容', trigger: 'blur'}],
  urgency: [{required: true, message: '请选择紧急程度', trigger: 'change'}],
});

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success('已发送给 AI 助理处理！');
      // 模拟 API 调用
      console.log('Sending to AI:', {user: props.targetUser?.name, ...form});
      emit('update:modelValue', false);
      formRef.value?.resetFields();
    }
  });
};
</script>