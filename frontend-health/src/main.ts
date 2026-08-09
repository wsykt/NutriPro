import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import axios from 'axios'
import App from './App.vue'
import './assets/style/tailwind.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.config.globalProperties.$axios = axios
app.mount('#app')
