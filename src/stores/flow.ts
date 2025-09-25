import {defineStore} from 'pinia'

export type MentalState = 'Flow' | 'Anxiety' | 'Arousal' | 'Worry' | 'Apathy' | 'Boredom' | 'Relaxation' | 'Control'

export interface EnergyPoint {
    id: string
    state: MentalState
    timestamp: number
}

export interface Highlight {
    id: string;
    author: string;
    content: string;
    timestamp: number;
    avatar: string;
}

export interface SkillNode {
    name: string;
    value: number; // 代表掌握度或经验值
    children?: SkillNode[];
}

export interface FlowStoreState {
    energyFeed: EnergyPoint[]
    insights: {
        boosters: { text: string; value: number }[]
        blockers: { text: string; value: number }[]
    }
    focusAnalytics: {
        deepWorkPercentage: number
        weeklyFocusHours: number[] // [周一, 周二, ...]
    }
    achievements: {
        highlights: Highlight[];
    };
    skillTree: SkillNode;
}

export const useFlowStore = defineStore('flow', {
    state: (): FlowStoreState => ({
        energyFeed: [],
        insights: {
            boosters: [
                {text: '需求清晰', value: 20},
                {text: '有效沟通', value: 15},
            ],
            blockers: [
                {text: '会议太多', value: 25},
                {text: '环境嘈杂', value: 18},
            ],
        },
        focusAnalytics: {
            deepWorkPercentage: 76,
            weeklyFocusHours: [4.5, 6, 5, 7, 3, 0, 0],
        },
        achievements: {
            highlights: [
                {
                    id: 'hl1',
                    author: 'Alice',
                    content: '解决了困扰一周的渲染性能问题，页面加载速度提升50%！🚀',
                    timestamp: Date.now() - 1000 * 60 * 30,
                    avatar: 'https://i.pravatar.cc/40?u=alice'
                },
                {
                    id: 'hl2',
                    author: 'Charlie',
                    content: '获得客户点名表扬，称赞我们的新功能设计得非常贴心。',
                    timestamp: Date.now() - 1000 * 60 * 60 * 2,
                    avatar: 'https://i.pravatar.cc/40?u=charlie'
                },
            ],
        },
        skillTree: {
            name: '团队技能',
            value: 100,
            children: [
                {
                    name: '前端', value: 80, children: [
                        {name: 'Vue.js', value: 70}, {name: 'TypeScript', value: 60}, {name: '可视化', value: 50}
                    ]
                },
                {
                    name: '后端', value: 90, children: [
                        {name: 'Node.js', value: 75}, {name: '数据库', value: 65}, {name: 'DevOps', value: 40}
                    ]
                },
                {
                    name: '产品与设计', value: 60, children: [
                        {name: 'UI/UX', value: 55}, {name: '用户研究', value: 30}
                    ]
                }
            ]
        },
    }),
    actions: {
        addEnergyPoint(state: MentalState) {
            const newPoint: EnergyPoint = {
                id: `point_${Date.now()}_${Math.random()}`,
                state,
                timestamp: Date.now(),
            }
            this.energyFeed.push(newPoint)
            // 模拟一段时间后自动消失
            setTimeout(() => {
                this.energyFeed.shift()
            }, 10000)
        },
        addInsight(type: 'booster' | 'blocker', text: string) {
            // 在真实项目中，这里会调用AI后端分析并更新词云数据
            // 这里我们做一个简单的模拟
            const target = type === 'booster' ? this.insights.boosters : this.insights.blockers
            const existing = target.find(item => item.text === text)
            if (existing) {
                existing.value += 5
            } else {
                target.push({text, value: 10})
            }
        },
        addHighlight(content: string) {
            const newHighlight: Highlight = {
                id: `hl_${Date.now()}`,
                author: '极客 A', // 从 userStore 获取
                content,
                timestamp: Date.now(),
                avatar: 'https://i.pravatar.cc/40?u=geekA'
            };
            this.achievements.highlights.unshift(newHighlight);

            import('canvas-confetti').then(confetti => {
                confetti.default({
                    particleCount: 100,
                    spread: 70,
                    origin: {y: 0.6}
                });
            });
        },
        getMeaningLink(taskName: string): string {
            const links = [
                `完成'${taskName}'，为我们Q3的目标“提升用户活跃度”贡献了关键一步！`,
                `太棒了！'${taskName}'的交付，让我们的产品在“易用性”上获得了巨大提升。`,
                `你刚刚完成的'${taskName}'，直接解决了我们最大客户提出的一个核心痛点。`,
            ];
            return links[Math.floor(Math.random() * links.length)]!;
        }
    },
})