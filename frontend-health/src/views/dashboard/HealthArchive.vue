<template>
  <div class="tab-page">
    <div class="tab-bar">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
        {{ t.label }}
      </button>
    </div>
    <keep-alive>
      <component :is="currentComponent" />
    </keep-alive>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MetricsHistory from './MetricsHistory.vue'
import HealthHistory from './HealthHistory.vue'

const route = useRoute()
const router = useRouter()

const tabs: { key: string; label: string; comp: Component }[] = [
  { key: 'metrics', label: '身体指标', comp: MetricsHistory },
  { key: 'records', label: '健康记录', comp: HealthHistory },
]

const activeTab = ref<string>((route.query.tab as string) || 'metrics')
const currentComponent = computed(() => tabs.find(t => t.key === activeTab.value)?.comp || MetricsHistory)

function switchTab(key: string) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}
watch(() => route.query.tab, (v) => { if (v && v !== activeTab.value) activeTab.value = v as string })
</script>

<style scoped>
.tab-page { min-height: 100%; }
.tab-bar {
  display: flex; gap: 0; border-bottom: 2px solid rgba(184,134,59,.14);
  margin-bottom: 20px; position: relative;
}
.tab-btn {
  font-size: 13px; font-weight: 600; color: rgba(42,38,32,.45);
  padding: 10px 22px 12px; cursor: pointer; border: none; background: none;
  transition: color .25s ease; position: relative;
}
.tab-btn:hover { color: rgba(42,38,32,.7); }
.tab-btn.active { color: #B8863B; }
.tab-btn.active::after {
  content: ''; position: absolute; bottom: -2px; left: 14px; right: 14px; height: 2px; border-radius: 2px;
  background: linear-gradient(90deg,#D9A24A,#B8863B);
}
</style>
