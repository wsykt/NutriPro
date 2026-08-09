<template>
  <div class="page-fade">
    <div class="mb-6">
      <h2 class="text-2xl font-bold mb-2 text-morandi-text">食谱库</h2>
      <p class="text-morandi-lightText mb-6 text-sm">浏览健康食谱，支持AI智能生成</p>
    </div>

    <!-- Tabs 切换 -->
    <div class="flex items-center gap-1 mb-6 bg-white/60 rounded-xl p-1 border border-morandi-soft/30 w-fit">
      <button
        @click="currentTab = 'all'"
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          currentTab === 'all'
            ? 'bg-morandi-accent text-white shadow-sm'
            : 'text-morandi-lightText hover:text-morandi-text'
        ]"
      >
        全部食谱
      </button>
      <button
        @click="currentTab = 'saved'; loadMySavedRecipes()"
        :class="[
          'px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          currentTab === 'saved'
            ? 'bg-morandi-accent text-white shadow-sm'
            : 'text-morandi-lightText hover:text-morandi-text'
        ]"
      >
        我的收藏
      </button>
    </div>

    <!-- 搜索栏和操作区 -->
    <div class="flex flex-wrap items-center gap-4 mb-6">
      <div class="flex-1 max-w-md">
        <input
          v-if="currentTab === 'all'"
          v-model="searchKeyword"
          @input="handleSearch"
          type="text"
          placeholder="搜索食谱..."
          class="w-full px-4 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none transition-all focus:border-morandi-accent"
        />
        <input
          v-else
          v-model="savedSearchKeyword"
          type="text"
          placeholder="搜索收藏的食谱..."
          class="w-full px-4 py-2 rounded-lg bg-white/70 border border-morandi-soft text-sm outline-none transition-all focus:border-morandi-accent"
        />
      </div>
      <div v-if="currentTab === 'all'" class="flex flex-wrap gap-2">
        <button
          v-for="tag in recipeTags"
          :key="tag"
          @click="selectTag(tag)"
          :class="[
            'px-3 py-2 rounded-full text-sm transition-all duration-200',
            selectedTags.includes(tag)
              ? 'bg-morandi-accent text-white shadow-sm scale-[1.02]'
              : 'bg-white/70 border border-morandi-soft text-morandi-text hover:bg-morandi-soft'
          ]"
        >
          {{ tag }}
        </button>
      </div>
      <button
        @click="showGenerateDialog = true"
        class="px-4 py-2 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 hover:scale-[1.02] transition-all shadow-sm"
      >
        AI生成食谱
      </button>
    </div>

    <!-- 食谱卡片列表 -->
    <div v-if="currentTab === 'all'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="recipe in recipes"
        :key="recipe.id"
        class="glass rounded-2xl p-6 hover:shadow-lg transition-shadow duration-300"
      >
        <h3 class="font-semibold text-lg text-morandi-text mb-2">{{ recipe.name }}</h3>
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
          @click="viewRecipe(recipe)"
          class="w-full mt-4 px-4 py-2 rounded-lg bg-morandi-accent/10 text-morandi-accent text-sm hover:bg-morandi-accent/20 transition-colors"
        >
          查看详情
        </button>
      </div>
    </div>

    <!-- 我的收藏卡片列表 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="recipe in filteredSavedRecipes"
        :key="recipe.id"
        class="glass rounded-2xl p-6 hover:shadow-lg transition-shadow duration-300"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="font-semibold text-lg text-morandi-text">{{ recipe.name }}</h3>
          <button
            @click="deleteMyRecipe(recipe.id)"
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
          @click="viewRecipe(recipe)"
          class="w-full mt-4 px-4 py-2 rounded-lg bg-morandi-accent/10 text-morandi-accent text-sm hover:bg-morandi-accent/20 transition-colors"
        >
          查看详情
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="(currentTab === 'all' && recipes.length === 0) || (currentTab === 'saved' && filteredSavedRecipes.length === 0)"
      class="text-center py-16 text-morandi-lightText"
    >
      <div class="text-6xl mb-4 opacity-60"><component :is="BookOpen" class="w-16 h-16 mx-auto" /></div>
      <p class="text-base">{{ currentTab === 'all' ? '暂无食谱，点击右上角「AI生成食谱」快速创建' : '暂无收藏的食谱，浏览全部食谱并收藏' }}</p>
    </div>

    <!-- AI生成食谱弹窗 -->
    <div v-if="showGenerateDialog">
      <Teleport to="body">
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            class="absolute inset-0 bg-black/35 backdrop-blur-[3px] mask-layer transition-opacity duration-200"
            @click="closeGenerateDialog"
          ></div>
          <div
            class="relative z-10 bg-white rounded-2xl w-full max-w-[680px] max-h-[80vh] overflow-auto shadow-xl dialog-fade scrollbar-hide"
            style="transform: translateZ(0);"
            @click.stop
          >
            <div class="p-8">
              <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-bold text-morandi-text">AI生成食谱</h3>
                <button
                  @click="closeGenerateDialog"
                  class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-morandi-soft text-morandi-lightText hover:text-morandi-text transition-colors text-lg"
                >
                  ✕
                </button>
              </div>

              <textarea
                v-model="generatePrompt"
                @input="promptError = ''"
                rows="4"
                placeholder="请描述您想要的食谱，例如：适合减脂的午餐食谱，需要高蛋白低热量..."
                class="w-full px-4 py-3 rounded-lg bg-white/70 border text-sm outline-none transition-all mb-2 resize-none"
                :class="promptError ? 'border-red-300 focus:border-red-500' : 'border-morandi-soft focus:border-morandi-accent'"
              ></textarea>

              <!-- 校验提示 -->
              <div
                v-if="promptError"
                class="flex items-start gap-2 mb-4 px-3 py-2.5 rounded-lg bg-amber-50 border border-amber-200 text-sm"
              >
                <component :is="Lightbulb" class="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <span class="text-amber-700">{{ promptError }}</span>
              </div>

              <div class="mb-8">
                <p class="text-xs text-morandi-lightText mb-3">人群标签：</p>
                <div class="flex flex-wrap gap-2.5">
                  <button
                    v-for="tag in personaTags"
                    :key="tag"
                    @click="selectedPersona = tag"
                    :class="[
                      'px-3 py-1.5 rounded-full text-xs transition-all duration-200',
                      selectedPersona === tag
                        ? 'bg-morandi-accent text-white shadow-sm'
                        : 'bg-morandi-soft text-morandi-text hover:bg-morandi-soft/70'
                    ]"
                  >
                    {{ tag }}
                  </button>
                </div>
              </div>

              <button
                @click="generateRecipe"
                :disabled="!generatePrompt.trim() || isGenerating"
                class="w-full px-4 py-3 rounded-lg bg-morandi-accent text-white font-medium hover:opacity-90 hover:scale-[1.01] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ isGenerating ? '生成中...' : '生成食谱' }}
              </button>

              <div
                v-if="generatedRecipe"
                class="mt-6 p-5 rounded-xl bg-morandi-soft/30 border border-morandi-soft/50"
              >
                <h4 class="font-semibold text-morandi-text mb-2 text-lg">{{ generatedRecipe.name }}</h4>
                <p class="text-sm text-morandi-lightText mb-3">{{ generatedRecipe.description }}</p>
                <div class="flex flex-wrap gap-2 mb-4">
                  <span
                    v-for="tag in generatedRecipe.tags"
                    :key="tag"
                    class="px-2 py-1 rounded-full bg-morandi-soft text-morandi-text text-xs"
                  >
                    {{ tag }}
                  </span>
                </div>

                <!-- 食材清单（带数据库匹配信息） -->
                <div class="text-sm mb-4">
                  <div class="font-medium text-morandi-text mb-2">食材清单：</div>
                  <ul class="text-morandi-lightText space-y-1.5">
                    <li
                      v-for="ing in generatedRecipe.ingredients"
                      :key="ing.ingredient_name"
                      class="flex items-center justify-between"
                    >
                      <span>{{ ing.ingredient_name }} {{ ing.amount }}{{ ing.unit }}</span>
                      <span v-if="getIngredientDBLabel(ing.ingredient_name)" class="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600 ml-2 flex-shrink-0">
                        {{ getIngredientDBLabel(ing.ingredient_name) }}
                      </span>
                      <span v-else class="text-xs text-morandi-lightText italic ml-2 flex-shrink-0">
                        待录入
                      </span>
                    </li>
                  </ul>
                </div>

                <!-- 烹饪步骤 -->
                <div v-if="generatedRecipe.steps && generatedRecipe.steps.length > 0" class="text-sm mb-4">
                  <div class="font-medium text-morandi-text mb-2">烹饪步骤：</div>
                  <ol class="text-morandi-lightText space-y-2 list-decimal list-inside">
                    <li v-for="(step, idx) in generatedRecipe.steps" :key="idx">
                      {{ step }}
                    </li>
                  </ol>
                </div>

                <!-- 营养成分简表 -->
                <div class="grid grid-cols-5 gap-2 text-center text-sm p-3 rounded-lg bg-white/50 mb-4">
                  <div>
                    <div class="text-xs text-morandi-lightText">热量</div>
                    <div class="font-bold text-morandi-accent">{{ generatedRecipe.calories }}kcal</div>
                  </div>
                  <div>
                    <div class="text-xs text-morandi-lightText">蛋白</div>
                    <div class="font-medium text-morandi-text">{{ generatedRecipe.protein }}g</div>
                  </div>
                  <div>
                    <div class="text-xs text-morandi-lightText">脂肪</div>
                    <div class="font-medium text-morandi-text">{{ generatedRecipe.fat }}g</div>
                  </div>
                  <div>
                    <div class="text-xs text-morandi-lightText">碳水</div>
                    <div class="font-medium text-morandi-text">{{ generatedRecipe.carbs }}g</div>
                  </div>
                  <div>
                    <div class="text-xs text-morandi-lightText">纤维</div>
                    <div class="font-medium text-morandi-text">{{ generatedRecipe.fiber }}g</div>
                  </div>
                </div>

                <div class="flex gap-3 mt-5">
                  <button
                    @click="saveGeneratedRecipe"
                    class="flex-1 px-4 py-2.5 rounded-lg bg-morandi-accent text-white text-sm hover:opacity-90 transition-opacity"
                  >
                    保存到我的食谱
                  </button>
                  <button
                    @click="generateRecipe"
                    :disabled="!generatePrompt.trim() || isGenerating"
                    class="flex-1 px-4 py-2.5 rounded-lg border border-morandi-soft text-morandi-text text-sm hover:bg-morandi-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    重新生成
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>

    <!-- 食谱详情弹窗 -->
    <div v-if="showDetailDialog">
      <Teleport to="body">
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            class="absolute inset-0 bg-black/35 backdrop-blur-[3px] mask-layer transition-opacity duration-200"
            @click="showDetailDialog = false"
          ></div>
          <div
            class="relative z-10 bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-auto shadow-xl dialog-fade scrollbar-hide"
            style="transform: translateZ(0);"
            @click.stop
          >
            <div class="p-8">
              <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-bold text-morandi-text">{{ selectedRecipe?.name }}</h3>
                <button
                  @click="showDetailDialog = false"
                  class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-morandi-soft text-morandi-lightText hover:text-morandi-text transition-colors text-lg"
                >
                  ✕
                </button>
              </div>
              <p class="text-morandi-lightText mb-6">{{ selectedRecipe?.description }}</p>
              <!-- 营养卡片：无替换显示每100g值，有替换显示总值+每100g值 -->
              <div class="mb-2">
                <div class="flex items-center justify-between text-xs text-morandi-lightText mb-2">
                  <span v-if="!hasSubstitutions">每100g 营养值</span>
                  <span v-else>替换后营养（总值 / 每100g）</span>
                  <span class="text-gray-400">≈{{ estimatedTotalWeight }}g/份</span>
                </div>
                <div class="grid grid-cols-4 gap-4 p-5 rounded-xl bg-morandi-soft/30">
                  <!-- 热量 -->
                  <div class="text-center">
                    <template v-if="hasSubstitutions">
                      <div class="text-lg font-bold" :class="modifiedNutrition.calories < originalNutritionSum.calories ? 'text-green-600' : 'text-red-600'">
                        {{ modifiedNutrition.calories }} kcal
                      </div>
                      <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.calories }} kcal</div>
                    </template>
                    <template v-else>
                      <div class="text-2xl font-bold text-morandi-accent">{{ selectedRecipe?.calories }}</div>
                      <div class="text-xs text-morandi-lightText">热量 (kcal)</div>
                    </template>
                  </div>
                  <!-- 蛋白质 -->
                  <div class="text-center">
                    <template v-if="hasSubstitutions">
                      <div class="text-lg font-bold" :class="modifiedNutrition.protein > originalNutritionSum.protein ? 'text-green-600' : 'text-morandi-text'">
                        {{ modifiedNutrition.protein }}g
                      </div>
                      <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.protein }}g</div>
                    </template>
                    <template v-else>
                      <div class="text-2xl font-bold text-morandi-text">{{ selectedRecipe?.protein }}</div>
                      <div class="text-xs text-morandi-lightText">蛋白质 (g)</div>
                    </template>
                  </div>
                  <!-- 脂肪 -->
                  <div class="text-center">
                    <template v-if="hasSubstitutions">
                      <div class="text-lg font-bold" :class="modifiedNutrition.fat < originalNutritionSum.fat ? 'text-green-600' : 'text-red-600'">
                        {{ modifiedNutrition.fat }}g
                      </div>
                      <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.fat }}g</div>
                    </template>
                    <template v-else>
                      <div class="text-2xl font-bold text-morandi-text">{{ selectedRecipe?.fat }}</div>
                      <div class="text-xs text-morandi-lightText">脂肪 (g)</div>
                    </template>
                  </div>
                  <!-- 碳水 -->
                  <div class="text-center">
                    <template v-if="hasSubstitutions">
                      <div class="text-lg font-bold text-morandi-text">{{ modifiedNutrition.carbs }}g</div>
                      <div class="text-xs text-gray-400">每100g: {{ modifiedPer100g.carbs }}g</div>
                    </template>
                    <template v-else>
                      <div class="text-2xl font-bold text-morandi-text">{{ selectedRecipe?.carbs }}</div>
                      <div class="text-xs text-morandi-lightText">碳水 (g)</div>
                    </template>
                  </div>
                </div>
              </div>
              <div class="mb-6">
                <h4 class="font-semibold text-morandi-text mb-3 flex items-center gap-2">
                  食材清单
                  <span v-if="hasSubstitutions" class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-normal">已智能替换</span>
                </h4>
                <ul class="space-y-2.5">
                  <li
                    v-for="(ing, index) in hasSubstitutions ? modifiedIngredients : (selectedRecipe?.ingredients || [])"
                    :key="index"
                    class="flex items-center justify-between p-3.5 rounded-lg transition-all duration-200"
                    :class="ing.isSubstituted ? 'bg-green-50 border border-green-200' : (isIngredientNotSuitable(ing) ? 'bg-red-50 border border-red-200' : 'bg-morandi-soft/20')"
                  >
                    <div class="flex items-center gap-2">
                      <!-- 已替换的食材 -->
                      <template v-if="ing.isSubstituted">
                        <span class="text-sm line-through text-gray-400">{{ ing.originalName }}</span>
                        <span class="text-gray-400">→</span>
                        <span class="text-green-700 font-medium">{{ ing.ingredientName }}</span>
                        <span class="px-1.5 py-0.5 text-xs font-bold bg-green-500 text-white rounded-full">已替换</span>
                      </template>
                      <!-- 未替换的食材 -->
                      <template v-else>
                        <span class="text-morandi-text">{{ ing.ingredientName || ing.ingredient_name }}</span>
                        <span v-if="isIngredientNotSuitable(ing)" class="px-1.5 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full">
                          不适合
                        </span>
                      </template>
                    </div>
                    <div class="flex items-center gap-2">
                      <span v-if="!ing.isSubstituted && getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name)" class="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-600">
                        {{ getIngredientDBLabel(ing.ingredientName || ing.ingredient_name || ing.name) }}
                      </span>
                      <span class="text-morandi-lightText">{{ ing.amount }}{{ ing.unit }}</span>
                    </div>
                  </li>
                </ul>
              </div>

              <!-- 烹饪步骤 -->
              <div v-if="selectedRecipe?.steps && selectedRecipe.steps.length > 0" class="mb-6">
                <h4 class="font-semibold text-morandi-text mb-3">烹饪步骤</h4>
                <ol class="space-y-2">
                  <li
                    v-for="(step, index) in selectedRecipe.steps"
                    :key="index"
                    class="flex items-start gap-3 p-3 rounded-lg bg-morandi-soft/20"
                  >
                    <span class="flex-shrink-0 w-6 h-6 rounded-full bg-morandi-accent text-white text-xs flex items-center justify-center mt-0.5">{{ Number(index) + 1 }}</span>
                    <span class="text-morandi-text text-sm">{{ step }}</span>
                  </li>
                </ol>
              </div>

              <!-- 规则基替换建议（过敏/口味） -->
              <div v-if="selectedRecipe?.substitutions?.length > 0" class="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200">
                <h4 class="font-semibold text-amber-800 mb-3 flex items-center gap-2">
                  <component :is="AlertTriangle" class="w-4 h-4" /> 食材替换建议（基于您的饮食档案）
                </h4>
                <div v-for="sub in selectedRecipe.substitutions" :key="sub.ingredient?.ingredientId || sub.ingredientName"
                  class="mb-3 p-3 rounded-lg bg-white/60 border border-amber-100 last:mb-0"
                >
                  <div class="flex items-center gap-2 text-sm mb-2">
                    <span class="text-amber-700 font-medium">{{ sub.ingredient?.ingredientName || sub.ingredientName }}</span>
                    <span class="text-amber-500 text-xs">{{ sub.reason }}</span>
                  </div>
                  <div v-if="sub.alternatives?.length > 0" class="flex flex-wrap gap-1.5">
                    <span class="text-xs text-gray-500 mr-1">推荐替代：</span>
                    <button
                      v-for="(alt, idx) in sub.alternatives"
                      :key="idx"
                      @click="applyIngredientSub(sub.ingredient?.ingredientName || sub.ingredientName, typeof alt === 'string' ? alt : alt.name)"
                      class="px-2.5 py-1 rounded-lg text-xs bg-white border border-amber-300 text-amber-700 hover:bg-amber-100 transition-colors"
                    >
                      {{ typeof alt === 'string' ? alt : alt.name }}
                      <span v-if="typeof alt !== 'string' && alt.benefit" class="opacity-70 ml-0.5">· {{ alt.benefit }}</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- 食物数据库基替换建议（高脂/高GI/高热量） -->
              <div v-if="selectedRecipe?.foodDbSubstitutions?.length > 0" class="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200">
                <h4 class="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  <span>🔬</span> 营养优化建议
                </h4>
                <div v-for="sub in selectedRecipe.foodDbSubstitutions" :key="sub.ingredientName"
                  class="mb-3 p-3 rounded-lg bg-white/60 border border-blue-100 last:mb-0"
                >
                  <div class="flex items-center gap-2 text-sm mb-2">
                    <span class="text-blue-700 font-medium">{{ sub.ingredientName }}</span>
                    <span class="text-red-500 text-xs">⚠ {{ (sub.concerns || []).join('、') }}</span>
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    <span class="text-xs text-gray-500 mr-1">推荐替代：</span>
                    <button
                      v-for="(alt, idx) in sub.alternatives"
                      :key="idx"
                      @click="applyNutritionSub(sub.ingredientName, alt)"
                      class="px-2.5 py-1 rounded-lg text-xs bg-white border border-blue-300 text-blue-700 hover:bg-blue-100 transition-colors"
                    >
                      {{ alt.name }}
                      <span class="opacity-70 ml-0.5">{{ alt.reason }}</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- 已应用的替换 -->
              <div v-if="hasSubstitutions" class="mb-6 p-4 rounded-xl bg-green-50 border border-green-200">
                <h4 class="font-semibold text-green-800 mb-2 flex items-center gap-2">
                  <component :is="Check" class="w-4 h-4" /> 已应用的替换
                </h4>
                <div v-for="(replaced, original) in appliedSubstitutions" :key="original"
                  class="flex items-center justify-between py-1.5 text-sm"
                >
                  <span class="text-gray-600">
                    <span class="line-through text-gray-400">{{ original }}</span>
                    <span class="mx-1.5">→</span>
                    <span class="text-green-700 font-medium">{{ typeof replaced === 'object' ? replaced.name : replaced }}</span>
                  </span>
                  <button @click="removeSubstitution(original)" class="text-xs text-red-400 hover:text-red-600">撤销</button>
                </div>
              </div>

              <!-- 营养变化对比 -->
              <div v-if="hasSubstitutions" class="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200">
                <h4 class="font-medium text-blue-800 mb-3 flex items-center gap-2">
                  <component :is="BarChart3" class="w-4 h-4" /> 替换前后营养对比
                </h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm text-center">
                    <thead>
                      <tr class="text-xs text-gray-500 border-b border-blue-100">
                        <th class="py-1.5 px-2 text-left">项目</th>
                        <th class="py-1.5 px-2">替换前</th>
                        <th class="py-1.5 px-2">替换后</th>
                        <th class="py-1.5 px-2">变化</th>
                      </tr>
                    </thead>
                    <tbody class="text-xs">
                      <tr class="border-b border-blue-50">
                        <td class="py-2 px-2 text-left font-medium text-gray-600">热量</td>
                        <td class="py-2 px-2">{{ originalNutritionSum.calories }} kcal</td>
                        <td class="py-2 px-2 font-medium" :class="modifiedNutrition.calories < originalNutritionSum.calories ? 'text-green-600' : 'text-red-600'">{{ modifiedNutrition.calories }} kcal</td>
                        <td class="py-2 px-2" :class="(modifiedNutrition.calories - originalNutritionSum.calories) < 0 ? 'text-green-600' : 'text-red-600'">
                          {{ (modifiedNutrition.calories - originalNutritionSum.calories) > 0 ? '+' : '' }}{{ modifiedNutrition.calories - originalNutritionSum.calories }}
                        </td>
                      </tr>
                      <tr class="border-b border-blue-50">
                        <td class="py-2 px-2 text-left font-medium text-gray-600">蛋白质</td>
                        <td class="py-2 px-2">{{ originalNutritionSum.protein }}g</td>
                        <td class="py-2 px-2 font-medium" :class="modifiedNutrition.protein > originalNutritionSum.protein ? 'text-green-600' : 'text-morandi-text'">{{ modifiedNutrition.protein }}g</td>
                        <td class="py-2 px-2" :class="(modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? 'text-green-600' : 'text-red-600'">
                          {{ (modifiedNutrition.protein - originalNutritionSum.protein) > 0 ? '+' : '' }}{{ (modifiedNutrition.protein - originalNutritionSum.protein).toFixed(1) }}
                        </td>
                      </tr>
                      <tr class="border-b border-blue-50">
                        <td class="py-2 px-2 text-left font-medium text-gray-600">脂肪</td>
                        <td class="py-2 px-2">{{ originalNutritionSum.fat }}g</td>
                        <td class="py-2 px-2 font-medium" :class="modifiedNutrition.fat < originalNutritionSum.fat ? 'text-green-600' : 'text-red-600'">{{ modifiedNutrition.fat }}g</td>
                        <td class="py-2 px-2" :class="(modifiedNutrition.fat - originalNutritionSum.fat) < 0 ? 'text-green-600' : 'text-red-600'">
                          {{ (modifiedNutrition.fat - originalNutritionSum.fat) > 0 ? '+' : '' }}{{ (modifiedNutrition.fat - originalNutritionSum.fat).toFixed(1) }}
                        </td>
                      </tr>
                      <tr class="border-b border-blue-50">
                        <td class="py-2 px-2 text-left font-medium text-gray-600">每100g热量</td>
                        <td class="py-2 px-2">{{ originalPer100g.calories }} kcal</td>
                        <td class="py-2 px-2 font-medium" :class="modifiedPer100g.calories < originalPer100g.calories ? 'text-green-600' : 'text-red-600'">{{ modifiedPer100g.calories }} kcal</td>
                        <td class="py-2 px-2" :class="(modifiedPer100g.calories - originalPer100g.calories) < 0 ? 'text-green-600' : 'text-red-600'">
                          {{ (modifiedPer100g.calories - originalPer100g.calories) > 0 ? '+' : '' }}{{ modifiedPer100g.calories - originalPer100g.calories }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p class="text-xs text-gray-400 mt-2">基于食材数据库估算，整份约 {{ estimatedTotalWeight }}g</p>
              </div>

              <div class="flex gap-3">
                <button
                  @click="saveRecipe(selectedRecipe)"
                  class="flex-1 px-4 py-2.5 rounded-lg bg-morandi-accent text-white hover:opacity-90 transition-opacity"
                >
                  保存到我的食谱
                </button>
                <button
                  @click="showDetailDialog = false"
                  class="flex-1 px-4 py-2.5 rounded-lg border border-morandi-soft text-morandi-text hover:bg-morandi-soft transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { api } from '@/api'
import { useRecipeStore } from '@/stores/recipe'
import { RECIPE_TAGS, RECIPE_PERSONA_TAGS } from '@/constants'
import { Lightbulb, BarChart3, BookOpen, Check, AlertTriangle } from 'lucide-vue-next'

const recipeStore = useRecipeStore()

const recipeTags = RECIPE_TAGS as unknown as string[]
const personaTags = RECIPE_PERSONA_TAGS as unknown as string[]

const currentTab = ref<'all' | 'saved'>('all')
const searchKeyword = ref('')
const savedSearchKeyword = ref('')
const selectedTags = ref<string[]>([])
const recipes = ref<any[]>([])
const showGenerateDialog = ref(false)
const showDetailDialog = ref(false)
const generatePrompt = ref('')
const promptError = ref('')
const selectedPersona = ref('普通用户')
const isGenerating = ref(false)
const generatedRecipe = ref<any>(null)
const selectedRecipe = ref<any>(null)
const mySavedRecipes = ref<any[]>([])
const enrichedIngredients = ref<Record<string, any>>({})

/** 搜索过滤我的收藏 */
const filteredSavedRecipes = computed(() => {
  if (!savedSearchKeyword.value.trim()) return mySavedRecipes.value
  const kw = savedSearchKeyword.value.toLowerCase().trim()
  return mySavedRecipes.value.filter((r: any) =>
    r.name?.toLowerCase().includes(kw) ||
    r.description?.toLowerCase().includes(kw) ||
    r.tags?.some((t: string) => t.toLowerCase().includes(kw))
  )
})

/** 校验AI生成食谱的输入 */
function validatePrompt(text: string): string {
  const trimmed = text.trim()
  if (trimmed.length < 4) {
    return '请输入更详细的需求描述，例如：「适合减脂的午餐，高蛋白低热量」或「用鸡胸肉和蔬菜做一道晚餐」'
  }
  // 纯数字/符号检测
  if (/^[\d\s\.\,\!\?\。\，\！\？\、\;\:\-\+\#\@\$\%\^\&\*\(\)\[\]\{\}]+$/.test(trimmed)) {
    return '请输入文字描述，例如说明想要的食谱类型（早/午/晚餐）、食材偏好和饮食目标'
  }
  // 检测是否包含食物相关关键词（如果完全没有，给出友好提示）
  const foodKeywords = /食|餐|饭|菜|肉|蛋|奶|豆|蔬|水|果|汤|粉|面|米|包|饺|炖|炒|炸|煎|蒸|煮|烤|拌|卤|低|高|减|增|健|营|养|热|蛋|白|脂|维|钙|铁|/
  if (!foodKeywords.test(trimmed)) {
    return '请描述您想要的食谱类型，例如：适合什么人群、想要什么口味、是否需要控制热量或蛋白质'
  }
  return '' // 校验通过
}

const appliedSubstitutions = reactive<Record<string, any>>({})

/** 是否有替换已应用 */
const hasSubstitutions = computed(() => Object.keys(appliedSubstitutions).length > 0)

/** 替换后的食材列表（原始食材+替换后结果） */
const modifiedIngredients = computed(() => {
  const base = selectedRecipe.value?.ingredients || []
  if (!hasSubstitutions.value) return base
  return base.map((ing: any) => {
    const name = ing.ingredientName || ing.ingredient_name || ing.name
    const sub = appliedSubstitutions[name]
    if (!sub) return ing
    return {
      ...ing,
      ingredientName: sub.name || sub,
      originalName: name,
      isSubstituted: true
    }
  })
})

/** 食材营养总和（原始值，用于对比基线） */
const originalNutritionSum = computed(() => {
  const recipe = selectedRecipe.value
  if (!recipe) return { calories: 0, protein: 0, fat: 0, carbs: 0 }
  let cal = 0, pro = 0, fat = 0, carb = 0
  for (const n of (recipe.ingredientNutrition || [])) {
    cal += (n.calories || 0)
    pro += (n.protein || 0)
    fat += (n.fat || 0)
    carb += (n.carbs || 0)
  }
  return { calories: Math.round(cal), protein: Math.round(pro * 10) / 10, fat: Math.round(fat * 10) / 10, carbs: Math.round(carb * 10) / 10 }
})

/** 估算整份菜品的总重量（g） */
const estimatedTotalWeight = computed(() => {
  const recipe = selectedRecipe.value
  if (!recipe?.ingredients) return 0
  let total = 0
  for (const ing of recipe.ingredients) {
    const amt = parseFloat(ing.amount) || 0
    const unit = (ing.unit || '').toLowerCase()
    if (unit === 'g' || unit === 'ml') total += amt
  }
  return total || 1 // 避免除零
})

/** 原始营养每 100g 值 */
const originalPer100g = computed(() => {
  const total = originalNutritionSum.value
  const w = estimatedTotalWeight.value
  return {
    calories: Math.round(total.calories / w * 100),
    protein: Math.round(total.protein / w * 100 * 10) / 10,
    fat: Math.round(total.fat / w * 100 * 10) / 10,
    carbs: Math.round(total.carbs / w * 100 * 10) / 10
  }
})

/** 替换后营养每 100g 值 */
const modifiedPer100g = computed(() => {
  const total = modifiedNutrition.value
  const w = estimatedTotalWeight.value
  return {
    calories: Math.round(total.calories / w * 100),
    protein: Math.round(total.protein / w * 100 * 10) / 10,
    fat: Math.round(total.fat / w * 100 * 10) / 10,
    carbs: Math.round(total.carbs / w * 100 * 10) / 10
  }
})

/** 替换后的营养总值（以 ingredientNutrition 实际食材数据为基数计算） */
const modifiedNutrition = computed(() => {
  const recipe = selectedRecipe.value
  if (!recipe || !hasSubstitutions.value) {
    return { calories: 0, protein: 0, fat: 0, carbs: 0 }
  }

  // 以 ingredientNutrition 总和为基数（不依赖 recipe.calories，那可能是份数估值而非实际食材和）
  let cal = 0, pro = 0, fat = 0, carb = 0

  // 建立食材名→营养值映射
  const nutritionMap = new Map<string, any>()
  for (const n of (recipe.ingredientNutrition || [])) {
    nutritionMap.set(n.ingredientName, n)
    cal += (n.calories || 0)
    pro += (n.protein || 0)
    fat += (n.fat || 0)
    carb += (n.carbs || 0)
  }

  // 逐个替换：减去原食材营养，加上替代品营养
  for (const [origName, sub] of Object.entries(appliedSubstitutions)) {
    const origNut = nutritionMap.get(origName)
    if (origNut) {
      cal -= (origNut.calories || 0)
      pro -= (origNut.protein || 0)
      fat -= (origNut.fat || 0)
      carb -= (origNut.carbs || 0)
    }

    // 替代品营养：per 100g × 用量
    const amount = origNut?.amount || 0
    const unit = origNut?.unit || 'g'
    const ratio = (unit === 'g' && amount > 0) ? amount / 100 : 1

    const subObj = typeof sub === 'object' ? sub : { name: sub }
    if (subObj.calories != null) cal += subObj.calories * ratio
    if (subObj.protein != null) pro += subObj.protein * ratio
    if (subObj.fat != null) fat += subObj.fat * ratio
    if (subObj.carbs != null) carb += subObj.carbs * ratio
  }

  return {
    calories: Math.round(cal),
    protein: Math.round(pro * 10) / 10,
    fat: Math.round(fat * 10) / 10,
    carbs: Math.round(carb * 10) / 10
  }
})

/** 判断食材是否被标记为"不适合" */
function isIngredientNotSuitable(ing: any): boolean {
  const name = ing.ingredientName || ing.ingredient_name || ing.name
  if (!name || !selectedRecipe.value?.substitutions) return false
  return selectedRecipe.value.substitutions.some((s: any) => {
    const subName = s.ingredient?.ingredientName || s.ingredient?.ingredient_name || s.ingredientName
    return subName === name && s.isNotSuitable
  })
}

/** 营养变化预估值（合并后端 + 已选替换） */
const nutritionChangeValue = computed(() => {
  const base = selectedRecipe.value?.nutritionChange || { calories: 0, fat: 0, protein: 0 }
  return {
    calories: base.calories || 0,
    fat: base.fat || 0,
    protein: base.protein || 0
  }
})

function applyIngredientSub(original: string, replaced: string) {
  // 尝试从 foodDbSubstitutions 查找该替代品的营养数据
  let altData: any = { name: replaced }
  if (selectedRecipe.value?.foodDbSubstitutions) {
    const dbSub = selectedRecipe.value.foodDbSubstitutions.find((s: any) => s.ingredientName === original)
    if (dbSub?.alternatives) {
      const matched = dbSub.alternatives.find((a: any) => a.name === replaced || a.name?.includes(replaced))
      if (matched) {
        altData = { name: matched.name, calories: matched.calories, protein: matched.protein, fat: matched.fat }
      }
    }
  }
  // 后备：尝试从食物数据库直接查找替代品的营养数据
  if (altData.calories == null && selectedRecipe.value?.ingredientDBInfo) {
    const info = selectedRecipe.value.ingredientDBInfo.find((i: any) =>
      i.name?.includes(replaced) || replaced.includes(i.name || '')
    )
    if (info) {
      altData = { name: info.name, calories: info.calories, protein: info.protein, fat: info.fat, carbs: info.carbs }
    }
  }
  // 仍无营养数据 → 保留原食材营养计算（使替换前后营养不变，比错误归零更合理）
  if (altData.calories == null) {
    const origNut = (selectedRecipe.value?.ingredientNutrition || []).find((n: any) => n.ingredientName === original)
    if (origNut) {
      altData = { name: replaced, calories: origNut.calories, protein: origNut.protein, fat: origNut.fat, carbs: origNut.carbs }
    }
  }
  appliedSubstitutions[original] = altData
}

function applyNutritionSub(original: string, replaced: any) {
  // replaced 来自 foodDbSubstitutions.alternatives，已含 name/calories/protein/fat
  appliedSubstitutions[original] = {
    name: replaced.name,
    calories: replaced.calories,
    protein: replaced.protein,
    fat: replaced.fat,
    carbs: replaced.carbs || 0
  }
}

function removeSubstitution(original: string) {
  delete appliedSubstitutions[original]
}

/** 转换系统食谱格式: recipeId→id, recipeName→name, tags字符串→数组 */
function normalizeRecipe(r: any): any {
  return {
    id: r.recipeId ?? r.id,
    name: r.recipeName ?? r.name ?? '',
    description: r.description ?? '',
    calories: r.calories ?? 0,
    protein: r.protein ?? 0,
    fat: r.fat ?? 0,
    carbs: r.carbs ?? 0,
    fiber: r.fiber ?? 0,
    tags: typeof r.tags === 'string' ? r.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : (r.tags || []),
    ingredients: r.ingredients || r.recipeIngredients || [],
    originalId: r.originalId,
    isSaved: r.isSaved
  }
}

/** 转换收藏食谱格式 */
function normalizeSavedRecipe(saved: any): any {
  let nutrition: any = {}
  if (saved.nutritionSummary) {
    try {
      nutrition = typeof saved.nutritionSummary === 'string' ? JSON.parse(saved.nutritionSummary) : saved.nutritionSummary
    } catch { nutrition = {} }
  }
  let ingredients: any[] = []
  if (saved.ingredients) {
    try {
      ingredients = typeof saved.ingredients === 'string' ? JSON.parse(saved.ingredients) : saved.ingredients
    } catch { ingredients = [] }
  }
  let steps: string[] = []
  if (saved.steps) {
    try {
      steps = typeof saved.steps === 'string' ? JSON.parse(saved.steps) : saved.steps
    } catch { steps = [] }
  }
  return {
    id: saved.id,
    name: saved.title,
    description: steps.length > 0 ? steps[0] : (nutrition.description || ''),
    steps: steps,
    calories: nutrition.calories || 0,
    protein: nutrition.protein || 0,
    fat: nutrition.fat || 0,
    carbs: nutrition.carbs || 0,
    fiber: nutrition.fiber || 0,
    tags: nutrition.tags || [],
    ingredients: ingredients,
    isSaved: true,
    originalId: saved.id,
    source: saved.source || ''
  }
}

const loadRecipes = async () => {
  try {
    const systemRecipes = await api.recipe.list()
    let allRecipes = systemRecipes.map(normalizeRecipe)

    try {
      const savedRecipesData = await api.recipe.mySaved()
      const savedRecipes = savedRecipesData
        .map(normalizeSavedRecipe)
        .filter((r: any) => r.source === 'generated')
      allRecipes = [...allRecipes, ...savedRecipes]
    } catch { /* ignore */ }

    recipes.value = allRecipes

    if (selectedTags.value.length > 0) {
      recipes.value = allRecipes.filter((r: any) =>
        r.tags?.some((t: string) => selectedTags.value.includes(t))
      )
    } else if (searchKeyword.value) {
      recipes.value = allRecipes.filter((r: any) =>
        r.name?.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
        r.description?.toLowerCase().includes(searchKeyword.value.toLowerCase())
      )
    }
  } catch (e) {
    console.error('加载食谱失败', e)
  }
}

const handleSearch = () => {
  selectedTags.value = []
  loadRecipes()
}

const selectTag = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index === -1) {
    selectedTags.value.push(tag)
  } else {
    selectedTags.value.splice(index, 1)
  }
  searchKeyword.value = ''
  loadRecipes()
}

const loadMySavedRecipes = async () => {
  try {
    await recipeStore.fetchFavorites()
    const data = await api.recipe.mySaved()
    mySavedRecipes.value = data.map(normalizeSavedRecipe)
  } catch (e) {
    console.error('加载我的食谱失败', e)
  }
}

const deleteMyRecipe = async (id: number) => {
  if (!confirm('确定删除这条食谱？')) return
  try {
    await api.recipe.deleteSaved(id)
    await loadMySavedRecipes()
    await loadRecipes()
    alert('删除成功')
  } catch (e: any) {
    console.error('删除食谱失败', e)
    alert('删除失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

const closeGenerateDialog = () => {
  showGenerateDialog.value = false
  generatePrompt.value = ''
  promptError.value = ''
  selectedPersona.value = '普通用户'
  generatedRecipe.value = null
}

const generateRecipe = async () => {
  // 输入校验
  const error = validatePrompt(generatePrompt.value)
  if (error) {
    promptError.value = error
    return
  }
  promptError.value = ''
  isGenerating.value = true
  try {
    let result = await api.ai.generateRecipe(generatePrompt.value)
    if (typeof result === 'string') {
      try {
        const jsonMatch = result.match(/```json\s*([\s\S]*?)\s*```/)
        if (jsonMatch) {
          result = JSON.parse(jsonMatch[1])
        } else {
          result = JSON.parse(result)
        }
      } catch {
        // fallback if not valid JSON string
      }
    }
    generatedRecipe.value = result
    // 生成成功后查找食材数据库信息
    if (result?.ingredients?.length > 0) {
      fetchIngredientDBInfo(result.ingredients.map((i: any) => i.ingredient_name))
    }
  } catch (e) {
    console.error('生成食谱失败', e)
    promptError.value = 'AI生成失败，请稍后重试'
  } finally {
    isGenerating.value = false
  }
}

/** 从food数据库批量查找食材营养信息 */
const fetchIngredientDBInfo = async (names: string[]) => {
  if (!names || names.length === 0) return
  try {
    const data = await api.food.batchLookup(names)
    if (data) {
      enrichedIngredients.value = { ...enrichedIngredients.value, ...data }
    }
  } catch (e) {
    console.warn('食材数据库查询失败', e)
  }
}

/** 获取食材的数据库信息展示文本 */
function getIngredientDBLabel(name: string): string {
  const food = enrichedIngredients.value[name]
  if (!food) return ''
  const cal = food.calorie ?? '-'
  return `[${food.foodCategory || '?'}] ${cal}kcal/100g`
}

const saveGeneratedRecipe = async () => {
  if (!generatedRecipe.value) return
  try {
    await api.recipe.save({
      title: generatedRecipe.value.name,
      steps: JSON.stringify(generatedRecipe.value.steps || []),
      ingredients: JSON.stringify(generatedRecipe.value.ingredients || []),
      nutritionSummary: JSON.stringify({
        calories: generatedRecipe.value.calories,
        protein: generatedRecipe.value.protein,
        fat: generatedRecipe.value.fat,
        carbs: generatedRecipe.value.carbs,
        fiber: generatedRecipe.value.fiber || 0,
        tags: generatedRecipe.value.tags || []
      }),
      source: 'generated'
    })
    alert('保存成功')
    closeGenerateDialog()
    loadRecipes()
  } catch (e: any) {
    console.error('保存食谱失败', e)
    alert('保存失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

const viewRecipe = async (recipe: any) => {
  selectedRecipe.value = recipe
  showDetailDialog.value = true
  // 重置替换状态
  Object.keys(appliedSubstitutions).forEach(k => delete appliedSubstitutions[k])
  
  // 如果是已收藏的食谱（替换后的版本），直接使用保存的数据，不获取替换建议
  if (recipe.isSaved) {
    return
  }
  
  // 获取食材数据库信息
  if (recipe.ingredients?.length > 0) {
    const names = recipe.ingredients.map((i: any) => i.ingredient_name || i.ingredientName || i.name).filter(Boolean)
    if (names.length > 0) fetchIngredientDBInfo(names)
  }
  // 获取替换建议
  try {
    const detail = await api.recipe.getDetail(recipe.id || recipe.originalId)
    if (detail) {
      if (detail.ingredients) selectedRecipe.value.ingredients = detail.ingredients
      selectedRecipe.value.substitutions = detail.substitutions || []
      selectedRecipe.value.foodDbSubstitutions = detail.foodDbSubstitutions || []
      // 新增：食材营养估算和营养变化
      selectedRecipe.value.ingredientNutrition = detail.ingredientNutrition || []
      selectedRecipe.value.nutritionChange = detail.nutritionChange || { hasChanges: false, calories: 0, fat: 0, protein: 0, replaceableCount: 0 }
      // 如有替换建议则同时查找食材DB
      const allSubNames = (detail.foodDbSubstitutions || []).flatMap((s: any) => 
        (s.alternatives || []).map((a: any) => a.name)
      )
      if (allSubNames.length > 0) fetchIngredientDBInfo(allSubNames)
    }
  } catch (e) {
    console.warn('获取食谱详情失败', e)
  }
}

const saveRecipe = async (recipe: any) => {
  if (!recipe) return
  try {
    const hasSubs = hasSubstitutions.value
    const ingredients = hasSubs ? modifiedIngredients.value : (recipe.ingredients || [])
    const nutrition = hasSubs ? {
      calories: modifiedNutrition.value.calories,
      protein: modifiedNutrition.value.protein,
      fat: modifiedNutrition.value.fat,
      carbs: modifiedNutrition.value.carbs,
      fiber: recipe.fiber || 0,
      tags: recipe.tags || []
    } : {
      calories: recipe.calories,
      protein: recipe.protein,
      fat: recipe.fat,
      carbs: recipe.carbs,
      fiber: recipe.fiber || 0,
      tags: recipe.tags || []
    }

    await recipeStore.toggleFavorite(recipe)
    showDetailDialog.value = false
    loadRecipes()
  } catch (e: any) {
    console.error('保存食谱失败', e)
    alert('保存失败：' + (e?.response?.data?.message || e?.message || '未知错误'))
  }
}

watch([showGenerateDialog, showDetailDialog], (newVal) => {
  if (newVal[0] || newVal[1]) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  loadRecipes()
})
</script>

<style scoped>
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.dialog-fade {
  animation: dialogFade 0.25s ease forwards;
  will-change: opacity, transform;
}
@keyframes dialogFade {
  from { opacity: 0; transform: scale(0.96) translateZ(0); }
  to { opacity: 1; transform: scale(1) translateZ(0); }
}
.mask-layer {
  will-change: backdrop-filter, opacity;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
@media (max-width: 768px) {
  .mask-layer { backdrop-filter: none !important; --tw-backdrop-blur: none !important; }
}
</style>
