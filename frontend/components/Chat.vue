<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg shadow-md overflow-hidden">
    <!-- Chat Messages -->
    <div ref="container" class="flex-1 p-4 overflow-y-auto space-y-4">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="flex items-start"
        :class="msg.from === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- Avatar -->
        <div
          class="max-w-[80%] p-4 rounded-lg prose dark:prose-invert"
          :class="msg.from === 'user'
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-none'"
        >
          <MarkdownComponent :content="msg.content" />
        </div>
      </div>

      <!-- Typing Indicator -->
      <div v-if="loading" class="flex items-center">
        <div class="flex space-x-1">
          <span class="w-2 h-2 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce-delay-0"></span>
          <span class="w-2 h-2 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce-delay-200"></span>
          <span class="w-2 h-2 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce-delay-400"></span>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex items-center space-x-2">
      <Textarea
        v-model="draft"
        placeholder="Type your message..."
        class="flex-1 resize-none"
        rows="1"
        @keydown.enter.stop.prevent="sendMessage"
        @input="autoResize"
      />
      <Button
        variant="primary"
        :disabled="!draft || loading"
        @click="sendMessage"
      >
        Send
      </Button>
      <Button
        v-if="loading"
        variant="outline"
        size="sm"
        class="text-red-500"
        @click="stopGeneration"
      >
        Stop
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUpdated, nextTick } from 'vue'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import MarkdownComponent from '~/components/MarkdownComponent.vue'

interface Message {
  from: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const draft = ref('')
const loading = ref(false)
let controller: AbortController | null = null

const container = ref<HTMLElement | null>(null)

function autoResize(event: Event) {
  const el = event.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

async function sendMessage() {
  const text = draft.value.trim()
  if (!text) return

  // Add user message
  messages.value.push({ from: 'user', content: text })
  draft.value = ''
  loading.value = true

  controller = new AbortController()
  const charDelay = 30
  let assistantContent = ''

  const runtimeConfig = useRuntimeConfig()
  const baseUrl = runtimeConfig.public.apiBase
  const runId = 'your-homework-run-id' // TODO: dynamically pass this, e.g. via route param

  const sendingMessages = messages.value.map(m => ({
    role: m.role || "user",
    content: m.content
  }))

  console.log("sendingMessages", sendingMessages)

  const jsonMessages = JSON.stringify(sendingMessages)
  console.log("jsonMessages", jsonMessages)

  try {
    const response = await fetch(`${baseUrl}/homework-assistant/chat/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonMessages,
      signal: controller.signal,
    })

    if (!response.ok || !response.body) {
      throw new Error('Failed to stream')
    }

    // Add assistant placeholder
    messages.value.push({ from: 'assistant', content: '' })
    const msgIndex = messages.value.length - 1

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      for (const char of chunk) {
        assistantContent += char
        messages.value[msgIndex].content = assistantContent
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, charDelay))
      }
    }

  } catch (e) {
    console.error(e)
    messages.value.push({ from: 'assistant', content: '[Error during response streaming]' })
  } finally {
    loading.value = false
    controller = null
  }
}


function stopGeneration() {
  if (controller) controller.abort()
}

// auto-scroll
onUpdated(() => {
  if (container.value) {
    container.value.scrollTop = container.value.scrollHeight
  }
})
</script>

<style scoped>
/* Typing bubble animation delays */
@keyframes bounce-delay {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}
.animate-bounce-delay-0 { animation: bounce-delay 1s infinite; }
.animate-bounce-delay-200 { animation: bounce-delay 1s infinite 0.2s; }
.animate-bounce-delay-400 { animation: bounce-delay 1s infinite 0.4s; }

/* Scrollbar styling */
.flex-1::-webkit-scrollbar { width: 6px; }
.flex-1::-webkit-scrollbar-thumb { background-color: rgba(100,100,100,0.4); border-radius: 3px; }
</style>
