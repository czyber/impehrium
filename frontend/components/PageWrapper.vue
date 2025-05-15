<template>
  <div class="flex flex-col h-full px-6 py-8 max-w-full mx-auto">
    <header v-if="title" class="mb-6">
      <h1 class="text-xl font-semibold">{{ title }}</h1>
    </header>

    <main class="flex-1">
      <slot />
    </main>
  </div>
</template>
<script setup>
import { useHead } from '#imports'

const props = defineProps({
  title: {
    type: String,
    default: ''
  }
})

useHead({
  title: props.title || undefined
})
</script>
