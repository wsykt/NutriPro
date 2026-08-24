<template>
  <div class="page-fade h-full flex flex-col">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold mb-2 text-morandi-text">AI健康咨询</h2>
        <p class="text-morandi-lightText text-sm">专业健康助手，提供饮食、运动、营养方面的建议</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        <span class="text-xs text-morandi-lightText">DeepSeek AI 在线</span>
      </div>
    </div>

    <div class="flex-1 glass rounded-2xl p-6 flex flex-col overflow-hidden">
      <div class="flex-1 overflow-y-auto space-y-4 mb-4" ref="messagesContainer">
        <div v-if="messages.length === 0 && !isLoading" class="flex flex-col items-center justify-center h-full text-center">
          <div class="w-16 h-16 rounded-full bg-morandi-accent/10 flex items-center justify-center mb-4">
            <span class="text-3xl"></span>
          </div>
          <h3 class="text-lg font-semibold text-morandi-text mb-2">您好！我是您的健康助手</h3>
          <p class="text-sm text-morandi-lightText mb-4">我将结合您的健康档案和营养学知识库，为您提供个性化膳食建议</p>
          <div class="flex flex-wrap justify-center gap-2">
            <button v-for="quick in quickQuestions" :key="quick" @click="inputMessage = quick" class="px-3 py-2 rounded-lg bg-morandi-soft/50 text-morandi-text text-xs hover:bg-morandi-soft transition-colors">
              {{ quick }}
            </button>
          </div>
        </div>

        <div v-for="msg in messages" :key="msg.id" :class="['flex gap-3', msg.role === 'user' ? 'flex-row-reverse' : '']">
          <div :class="['w-10 h-10 rounded-full flex items-center justify-center shrink-0', msg.role === 'user' ? 'bg-morandi-accent text-white' : 'bg-morandi-soft text-morandi-accent']">
            {{ msg.role === 'user' ? '我' : 'AI' }}
          </div>
          <div :class="['max-w-[80%] p-4 rounded-2xl', msg.role === 'user' ? 'bg-morandi-accent text-white rounded-tr-none' : 'bg-white/70 text-morandi-text rounded-tl-none']">
            <p v-if="msg.content" class="whitespace-pre-wrap text-sm">{{ msg.content }}</p>
            <div v-if="msg.streaming" class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-morandi-accent animate-bounce"></span>
              <span class="w-2 h-2 rounded-full bg-morandi-accent animate-bounce" style="animation-delay: 0.1s"></span>
              <span class="w-2 h-2 rounded-full bg-morandi-accent animate-bounce" style="animation-delay: 0.2s"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-morandi-soft pt-4">
        <div class="flex gap-3">
          <textarea v-model="inputMessage" @keydown.enter.exact.prevent="sendMessage" rows="2" placeholder="向AI健康助手提问..." class="flex-1 px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft text-sm outline-none focus:border-morandi-accent resize-none"></textarea>
          <button @click="sendMessage" :disabled="!inputMessage.trim() || isLoading" class="px-6 py-3 rounded-xl bg-morandi-accent text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            <span v-if="isLoading">发送中...</span>
            <span v-else>发送</span>
          </button>
        </div>
        <p class="text-xs text-morandi-lightText mt-2 text-center">仅供膳食营养参考，不替代专业医疗诊断</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  streaming: boolean
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const quickQuestions = [
  '今天营养摄入达标了吗？',
  '给我推荐一份高蛋白质的午餐食谱',
  '糖尿病患者适合吃哪些主食？',
  '如何提高免疫力？',
  '运动后多久可以进食？',
  '老年人适合什么运动？'
]

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMsg: Message = {
    id: Date.now(),
    role: 'user',
    content: inputMessage.value.trim(),
    streaming: false
  }
  messages.value.push(userMsg)
  inputMessage.value = ''

  const assistantMsg: Message = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    streaming: true
  }
  messages.value.push(assistantMsg)

  await scrollToBottom()
  isLoading.value = true

  try {
    const url = `/api/ai/chat-stream?message=${encodeURIComponent(userMsg.content)}`
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      }
    })

    if (!response.ok) {
      throw new Error('网络请求失败')
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法获取响应流')
    }

    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          assistantMsg.content += data
          await scrollToBottom()
        }
      }
    }
  } catch (e) {
    console.error('AI对话失败', e)
    assistantMsg.content = '抱歉，AI服务暂时不可用，请稍后再试。\n\n建议您注意以下几点：\n1. 保证充足的蛋白质摄入\n2. 多吃蔬菜水果补充维生素\n3. 控制碳水化合物的摄入量\n4. 适量运动，保持身体健康'
  } finally {
    assistantMsg.streaming = false
    isLoading.value = false
    await scrollToBottom()
  }
}

onMounted(() => {})
</script>

<style scoped>
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-bounce {
  animation: bounce 1s infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>