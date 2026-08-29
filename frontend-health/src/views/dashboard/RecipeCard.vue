<template>
  <div class="rk-card" @click="$emit('view', recipe)">
    <span class="cover">
      <span v-if="isAi" class="ai" title="AI 炼成"><Sparkles :size="10" /></span>
      <b>{{ coverChar }}</b>
      <i class="tag">{{ coverTag }}</i>
    </span>
    <span class="meta">
      <h5>{{ recipe.name }} <BadgeCheck :size="11" /></h5>
      <p>{{ recipe.description }}</p>
      <span class="ntr">
        <b>{{ recipe.calories }}<i>kcal</i></b>
        <em class="p">蛋白 {{ recipe.protein }}g</em>
        <em class="f">脂肪 {{ recipe.fat }}g</em>
        <em class="c">碳水 {{ recipe.carbs }}g</em>
      </span>
      <span v-if="recipe.tags?.length" class="auds">
        <i v-for="t in recipe.tags" :key="t">{{ t }}</i>
      </span>
      <span class="go">{{ recipe.isSaved ? '已入匣 · ' : '查看食单 · ' }}星宴详情 <ChevronRight :size="11" /></span>
    </span>
    <button v-if="showDelete" class="del" title="删除" @click.stop="$emit('delete', recipe.id)">
      <X :size="12" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sparkles, BadgeCheck, ChevronRight, X } from 'lucide-vue-next'

const props = defineProps<{
  recipe: any
  showDelete?: boolean
}>()

defineEmits<{
  (e: 'view', recipe: any): void
  (e: 'delete', id: number): void
}>()

const coverChar = computed(() => props.recipe?.name?.slice(0, 1) || '食')
const coverTag = computed(() => props.recipe?.tags?.[0] || '食谱')
const isAi = computed(() => props.recipe?.source === 'generated')
</script>

<style scoped>
/* 星宴卡 · 星膳书阁（P10-A） */
@keyframes rkRise {
  from { opacity: 0; transform: translateY(18px) scale(.98); }
  to { opacity: 1; transform: none; }
}
.rk-card {
  position: relative; display: flex; text-align: left;
  border: 1px solid rgba(184, 134, 59, .35); border-radius: 14px;
  overflow: hidden; background: #FDFAF3;
  transition: transform .35s, border-color .35s, box-shadow .35s;
  cursor: pointer; color: #55503F;
  animation: rkRise .55s ease backwards;
}
.rk-card:hover {
  transform: translateY(-3px); border-color: rgba(184, 134, 59, .7);
  box-shadow: 0 16px 32px -16px rgba(46, 42, 34, .35), 0 0 18px rgba(184, 134, 59, .12);
}
/* 字纹封面 */
.cover {
  width: 74px; flex-shrink: 0; position: relative;
  display: flex; align-items: center; justify-content: center;
  background:
    radial-gradient(circle at 30% 22%, rgba(184, 134, 59, .16), transparent 68%),
    linear-gradient(160deg, #F5EDDA, #EFE2C4);
}
.cover::after {
  content: ''; position: absolute; inset: 0;
  background-image: radial-gradient(rgba(184, 134, 59, .35) 1px, transparent 1.5px);
  background-size: 17px 17px; opacity: .3;
}
.cover b {
  position: relative; z-index: 2;
  font-family: 'Noto Serif SC', serif; font-size: 30px; font-weight: 900;
  color: #B8863B; text-shadow: 0 2px 10px rgba(184, 134, 59, .3);
}
.cover .tag {
  position: absolute; bottom: 5px; left: 0; right: 0; z-index: 2;
  text-align: center; font-style: normal; font-size: 8.5px;
  letter-spacing: .16em; color: #A08F6E;
}
.cover .ai {
  position: absolute; top: 5px; right: 6px; z-index: 3;
  color: #B8863B; display: inline-flex;
  filter: drop-shadow(0 0 5px rgba(184, 134, 59, .7));
}
/* 信息区 */
.meta { padding: 11px 12px; min-width: 0; flex: 1; display: block; }
.meta h5 {
  font-size: 13.5px; font-weight: 700; color: #2E2A22; letter-spacing: .03em;
  display: flex; align-items: center; gap: 6px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.meta h5 svg { color: #A0722F; flex-shrink: 0; }
.meta p {
  font-size: 10.8px; line-height: 1.7; color: #847C63; margin-top: 4px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
/* 营养三色码：蛋白蓝 / 脂肪金 / 碳水绿 */
.ntr { display: flex; align-items: baseline; gap: 9px; margin-top: 8px; flex-wrap: wrap; }
.ntr b {
  font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 900; color: #B8863B;
}
.ntr b i { font-style: normal; font-size: 8.5px; color: #A08F6E; margin-left: 2px; letter-spacing: .06em; }
.ntr em {
  font-style: normal; font-size: 9.5px; color: #847C63;
  display: inline-flex; align-items: center; gap: 3.5px; white-space: nowrap;
}
.ntr em::before { content: ''; width: 5px; height: 5px; border-radius: 50%; display: inline-block; }
.ntr em.p::before { background: #4A6FA5; }
.ntr em.f::before { background: #C08A2D; }
.ntr em.c::before { background: #5E8F5E; }
.auds { margin-top: 7px; display: flex; gap: 4px; flex-wrap: wrap; }
.auds i {
  font-style: normal; font-size: 9px; padding: 1.5px 7px; border-radius: 99px;
  background: rgba(184, 134, 59, .1); color: #8a6d3b; border: 1px solid rgba(184, 134, 59, .28);
}
.go {
  margin-top: 8px; font-size: 10.5px; color: #B8863B;
  display: inline-flex; align-items: center; gap: 3px; font-weight: 600;
}
.go svg { transition: .25s; }
.rk-card:hover .go svg { transform: translateX(3px); }
/* 删除（我的收藏视图） */
.del {
  position: absolute; top: 8px; right: 8px; z-index: 4;
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid rgba(184, 134, 59, .4); background: rgba(248, 242, 227, .92);
  color: #A08F6E; display: flex; align-items: center; justify-content: center;
  transition: .25s; cursor: pointer;
}
.del:hover { color: #B5442E; border-color: #B5442E; transform: rotate(90deg); }
</style>
