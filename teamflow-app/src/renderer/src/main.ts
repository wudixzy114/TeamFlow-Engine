import {createApp} from 'vue';
import {createPinia} from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';

import App from './App.vue';
import router from './router';

// 引入 UnoCSS
import 'virtual:uno.css';
import './styles/style.css';
import './styles/markdown.css';
import './styles/markdown-theme.css'
import {VChart} from './plugins/echarts';

const app = createApp(App);
const pinia = createPinia();
pinia.use(piniaPluginPersistedstate); // 使用持久化插件

app.use(pinia);
app.use(router);

app.component('v-chart', VChart);

app.mount('#app');
