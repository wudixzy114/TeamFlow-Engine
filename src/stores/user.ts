import {defineStore} from 'pinia'
import {ElNotification} from "element-plus";

export interface UserState {
    name: string
    isInFlowMode: boolean
}

export const useUserStore = defineStore('user', {
    state: (): UserState => ({
        name: '极客 A', // 模拟一个用户
        isInFlowMode: false,
    }),
    actions: {
        toggleFlowMode() {
            this.isInFlowMode = !this.isInFlowMode
            // 真实的 API 调用会在这里
            // await api.setUserStatus(this.isInFlowMode)

            ElNotification({
                title: this.isInFlowMode ? '心流模式已开启' : '心流模式已关闭',
                message: this.isInFlowMode ? '系统将为您屏蔽干扰，祝您工作愉快！' : '欢迎回来！',
                type: this.isInFlowMode ? 'success' : 'info',
                duration: 2000,
            })
        },
    },
})