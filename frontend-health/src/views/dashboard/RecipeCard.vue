<template>
  <div class="glass rounded-2xl p-6 hover:shadow-lg transition-shadow duration-300">
    <div class="flex items-start justify-between mb-2">
      <h3 class="font-semibold text-lg text-morandi-text">{{ recipe.name }}</h3>
      <button
        v-if="showDelete"
        @click="$emit('delete', recipe.id)"
        class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full hover:bg-red-50 text-morandi-lightText hover:text-red-500 transition-colors text-sm"
        title="删除"
      >
        🗑
      </button>
    </div>
    <p class="text-sm text-morandi-lightText mb-4 line-clamp-2">{{ recipe.description }}</p>
    <div class="flex flex-wrap gap-1 mb-4">
      <span
        v-for="tag in recipe.tags"
        :key="tag"
        class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs"
      >
        {{ tag }}
      </span>
    </div>
    <div class="grid grid-cols-4 gap-2 text-center text-sm">
      <div>
        <div class="text-xs text-morandi-lightText">热量</div>
        <div class="font-bold text-morandi-accent">{{ recipe.calories }} kcal</div>
      </div>
      <div>
        <div class="text-xs text-morandi-lightText">蛋白</div>
        <div class="font-medium text-morandi-text">{{ recipe.protein }}g</div>
      </div>
      <div>
        <div class="text-xs text-morandi-lightText">脂肪</div>
        <div class="font-medium text-morandi-text">{{ recipe.fat }}g</div>
      </div>
      <div>
        <div class="text-xs text-morandi-lightText">碳水</div>
        <div class="font-medium text-morandi-text">{{ recipe.carbs }}g</div>
      </div>
    </div>
    <button
      @click="$emit('view', recipe)"
      class="w-full mt-4 px-4 py-2 rounded-lg bg-morandi-accent/10 text-morandi-accent text-sm hover:bg-morandi-accent/20 transition-colors"
    >
      查看详情
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  recipe: any
  showDelete?: boolean
}>()

defineEmits<{
  (e: 'view', recipe: any): void
  (e: 'delete', id: number): void
}>()
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
