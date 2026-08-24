<template>
  <div class="dietary-profile">
    <h1>我的饮食档案</h1>
    
    <div class="profile-form">
      <div class="form-section">
        <h2>过敏食材</h2>
        <p class="section-desc">请列出您对哪些食材过敏，系统将在菜谱中自动避开这些食材</p>
        <input 
          v-model="form.allergicFoods" 
          type="text" 
          placeholder="例如：花生, 海鲜, 牛奶"
        />
        <div class="help-text">多个食材用英文逗号分隔</div>
      </div>
      
      <div class="form-section">
        <h2>饮食禁忌</h2>
        <p class="section-desc">请选择您的饮食限制条件</p>
        <div class="checkbox-group">
          <label v-for="item in restrictionOptions" :key="item.value" class="checkbox-item">
            <input 
              type="checkbox" 
              :value="item.value"
              v-model="selectedRestrictions"
            />
            <span>{{ item.label }}</span>
          </label>
        </div>
      </div>
      
      <div class="form-section">
        <h2>口味偏好</h2>
        <p class="section-desc">请选择您的口味偏好，系统将根据您的偏好推荐菜谱</p>
        <div class="radio-group">
          <label v-for="item in tasteOptions" :key="item.value" class="radio-item">
            <input 
              type="radio" 
              name="tastePreference"
              :value="item.value"
              v-model="form.tastePreference"
            />
            <span>{{ item.label }}</span>
          </label>
        </div>
      </div>
      
      <div class="form-actions">
        <button class="save-btn" @click="saveProfile">保存饮食档案</button>
      </div>
    </div>
    
    <div v-if="saved" class="success-message flex items-center gap-2">
      <component :is="Check" class="w-4 h-4 text-green-500" /> 饮食档案已保存成功
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { api } from '@/api'
import { Check } from 'lucide-vue-next'

const form = ref({
  allergicFoods: '',
  dietaryRestrictions: '',
  tastePreference: '清淡'
})

const selectedRestrictions = ref<string[]>([])

const saved = ref(false)

const restrictionOptions = [
  { value: '低脂', label: '低脂饮食' },
  { value: '低盐', label: '低盐饮食' },
  { value: '低糖', label: '低糖饮食' },
  { value: '糖尿病', label: '糖尿病饮食' },
  { value: '无辣椒', label: '无辣椒' },
  { value: '素食', label: '素食' }
]

const tasteOptions = [
  { value: '清淡', label: '清淡' },
  { value: '适中', label: '适中' },
  { value: '重口味', label: '重口味' },
  { value: '微辣', label: '微辣' },
  { value: '辣', label: '辣' }
]

onMounted(() => {
  loadProfile()
})

async function loadProfile() {
  try {
    const data = await api.profile.getInfo()
    form.value.allergicFoods = data.allergicFoods || ''
    form.value.dietaryRestrictions = data.dietaryRestrictions || ''
    form.value.tastePreference = data.tastePreference || '清淡'

    if (form.value.dietaryRestrictions) {
      selectedRestrictions.value = form.value.dietaryRestrictions.split(',').map(s => s.trim())
    }
  } catch (e) {
    console.error('加载用户信息失败', e)
  }
}

watch(selectedRestrictions, (val) => {
  form.value.dietaryRestrictions = val.join(',')
})

async function saveProfile() {
  try {
    await api.profile.updateDietary({
      allergicFoods: form.value.allergicFoods,
      dietaryRestrictions: form.value.dietaryRestrictions,
      tastePreference: form.value.tastePreference
    })
    saved.value = true
    setTimeout(() => {
      saved.value = false
    }, 3000)
  } catch (e) {
    console.error('保存饮食档案失败', e)
    alert('保存失败，请重试')
  }
}
</script>

<style scoped>
.dietary-profile {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.dietary-profile h1 {
  font-size: 28px;
  margin-bottom: 30px;
  color: #333;
  text-align: center;
}

.profile-form {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.form-section {
  margin-bottom: 28px;
}

.form-section h2 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #333;
}

.section-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

.form-section input[type="text"] {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  box-sizing: border-box;
}

.form-section input[type="text"]:focus {
  outline: none;
  border-color: #2F5D4A;
}

.help-text {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.checkbox-group, .radio-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.checkbox-item, .radio-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.checkbox-item:hover, .radio-item:hover {
  background: #e9ecef;
}

.checkbox-item input[type="checkbox"],
.radio-item input[type="radio"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.checkbox-item span, .radio-item span {
  font-size: 14px;
  color: #333;
}

.form-actions {
  margin-top: 30px;
}

.save-btn {
  width: 100%;
  padding: 14px;
  background: #2F5D4A;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover {
  background: #274d3d;
}

.success-message {
  margin-top: 20px;
  padding: 16px;
  background: #E4EDE7;
  color: #2F5D4A;
  border-radius: 8px;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
}
</style>