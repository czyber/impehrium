<template>
  <div v-html="renderedHtml" class="prose max-w-none markdown dark:prose-invert"></div>
</template>

<script setup>
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';
import mk from 'markdown-it-katex';

const props = defineProps({
  content: {
    type: String,
    required: true
  }
});

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
}).use(mk);

const renderedHtml = computed(() => md.render(props.content));
</script>
