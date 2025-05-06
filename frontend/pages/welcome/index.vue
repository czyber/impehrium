<template>
  <PageWrapper title="Home">
    <div>
      <h1 class="text-xl font-semibold mb-4 text-gray-700">
        Welcome back, {{currentUser.first_name}}
      </h1>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
      <Card v-for="action in actions" :key="action.title" class="cursor-pointer hover:shadow-md transition">
        <CardContent class="flex items-center gap-4 p-4" @click="action.onClick">
          <component :is="action.icon" class="w-6 h-6 text-blue-600" />
          <div>
            <p class="font-medium">{{ action.title }}</p>
            <p class="text-sm text-gray-500">{{ action.subtitle }}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  </PageWrapper>
</template>

<script setup lang="ts">
import { Card, CardContent } from '@/components/ui/card'
import { Lightbulb, UploadCloud, NotebookPen, Brain } from 'lucide-vue-next'
import {useUserStore} from "~/stores/user-store.ts";
import PageWrapper from "~/components/PageWrapper.vue";

const userStore = useUserStore()
await userStore.fetchUser()

const {currentUser} = storeToRefs(userStore)


const actions = [
  {
    title: 'Ask a Question',
    subtitle: 'Get help with a problem',
    icon: Lightbulb,
    onClick: () => console.log('Ask clicked'),
  },
  {
    title: 'Upload Homework',
    subtitle: 'LLM will help explain it',
    icon: UploadCloud,
    onClick: () => console.log('Upload clicked'),
  },
  {
    title: 'Practice Exercises',
    subtitle: 'Reinforce tricky topics',
    icon: NotebookPen,
    onClick: () => console.log('Practice clicked'),
  },
  {
    title: 'Start a Quiz',
    subtitle: 'Evaluate understanding',
    icon: Brain,
    onClick: () => console.log('Quiz clicked'),
  },
]
</script>
