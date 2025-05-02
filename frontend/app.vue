<template>
  <div class="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center gap-6 p-6">
    <h1 class="text-3xl font-bold">Stellar Server Manager</h1>

    <button @click="createServer" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
      Create Server
    </button>

    <button @click="deleteServer" :disabled="!serverId" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded disabled:opacity-50">
      Delete Server
    </button>

    <div v-if="server" class="mt-4 p-4 border border-gray-700 rounded bg-gray-800 w-full max-w-md">
      <p><strong>ID:</strong> {{ server.id }}</p>
      <p><strong>Name:</strong> {{ server.name }}</p>
      <p><strong>Started:</strong> {{ server.started_at }}</p>
      <p><strong>Ended:</strong> {{ server.ended_at }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const api = config.public.apiBase

const server = ref(null)
const serverId = ref("")

async function createServer() {
  const response = await $fetch(`${api}/server`, {
    method: 'POST',
    body: { name: "New Game Server" },
  })
  server.value = response
  serverId.value = response.id
}

async function deleteServer() {
  if (!serverId.value) return

  const response = await $fetch(`${api}/server/${serverId.value}`, {
    method: 'DELETE',
  })
  server.value = response
  serverId.value = ""
}
</script>
