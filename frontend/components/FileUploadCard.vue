<script setup lang="ts">
import {useHomeworkAssistantStore} from "~/stores/homework-assistant-store";

const homeworkAssistantStore = useHomeworkAssistantStore()
const { fileUploaded, selectedFile } = storeToRefs(homeworkAssistantStore)

const emit = defineEmits<{
  upload: [file: File]
}>()


function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function onUpload() {
  if (!selectedFile.value) return
  fileUploaded.value = true
  emit('upload', selectedFile.value)
}
</script>

<template>
  <Card v-if="!fileUploaded" class="max-w-1/2 overflow-hidden">
    <CardHeader>
      <CardTitle>AI Homework Assistant</CardTitle>
      <CardDescription>
        Upload homework to get help from our AI homework assistant.
      </CardDescription>
    </CardHeader>
    <CardContent>
      Our artificial intelligence assistant will analyze the provided
      homework and offer assistance in understanding and solving the task.
    </CardContent>
    <CardFooter>
      <div class="grid w-full max-w-sm items-center gap-1.5">
        <Label for="file">File</Label>
        <Input id="file" type="file" @change="onFileChange" />
        <Button @click="onUpload" :disabled="!selectedFile">Upload file</Button>
      </div>
    </CardFooter>
  </Card>
</template>

