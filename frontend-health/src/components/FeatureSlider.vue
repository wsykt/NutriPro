<script setup lang="ts">
import { ref, computed } from 'vue'

interface Slide {
  title?: string
  description?: string
  tags?: string[]
  date?: string
  imageType?: 'grid' | 'card'
}

const props = defineProps<{
  slides: Slide[]
}>()

const current = ref(0)
const total = computed(() => props.slides.length)
const isFading = ref(false)

const goTo = (idx: number) => {
  let target = idx
  if (target < 0) target = total.value - 1
  if (target >= total.value) target = 0
  if (target === current.value) return
  isFading.value = true
  setTimeout(() => {
    current.value = target
    isFading.value = false
  }, 500)
}

const trackStyle = computed(() => ({
  transform: `translateX(-${current.value * 100}%)`,
  opacity: isFading.value ? 0 : 1,
  transition: 'opacity 0.5s ease',
}))
</script>

<template>
  <div class="relative w-full">
    <div class="overflow-hidden relative rounded-2xl glass p-6">
      <div
        class="absolute inset-0 pointer-events-none z-[2] transition-opacity duration-500"
        :class="isFading ? 'opacity-100' : 'opacity-0'"
        :style="{ background: 'linear-gradient(90deg, transparent 0%, rgba(248,251,249,0.65) 45%, rgba(248,251,249,0.95) 100%)' }"
      ></div>
      <div class="flex" :style="trackStyle">
        <div
          v-for="(slide, idx) in slides"
          :key="idx"
          class="flex-shrink-0 w-full px-4"
        >
          <div v-if="slide.imageType === 'grid'" class="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            <div v-for="n in 4" :key="n" class="aspect-square rounded-xl glass"></div>
          </div>
          <div v-else class="rounded-xl glass p-6 mx-auto" :class="slide.date ? 'max-w-xl' : 'max-w-md'">
            <div v-if="!slide.date" class="w-full h-48 rounded-xl bg-morandi-soft mb-6"></div>
            <h3 class="font-semibold text-2xl mb-3">{{ slide.title }}</h3>
            <p class="text-morandi-lightText text-base mb-6">{{ slide.description }}</p>
            <div v-if="slide.tags && slide.tags.length" class="flex gap-3 flex-wrap">
              <span v-for="tag in slide.tags" :key="tag" class="px-3 py-1 bg-morandi-soft rounded text-sm">{{ tag }}</span>
            </div>
            <span v-if="slide.date" class="text-sm text-morandi-lightText">{{ slide.date }}</span>
          </div>
        </div>
      </div>
    </div>

    <button
      @click="goTo(current - 1)"
      class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white"
    >
      ‹
    </button>
    <button
      @click="goTo(current + 1)"
      class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 glass w-11 h-11 rounded-full flex items-center justify-center z-10 text-2xl font-bold text-morandi-text hover:bg-white"
    >
      ›
    </button>

    <div class="flex justify-center gap-2 mt-6">
      <button
        v-for="(_, idx) in slides"
        :key="idx"
        @click="goTo(idx)"
        class="w-3 h-3 rounded-full cursor-pointer transition-colors"
        :class="idx === current ? 'bg-morandi-accent' : 'bg-morandi-soft hover:bg-morandi-accent/50'"
      ></button>
    </div>
  </div>
</template>
