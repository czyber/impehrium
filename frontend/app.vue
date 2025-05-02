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
import type { paths } from '~/types/api'

const config = useRuntimeConfig()
const api = config.public.apiBase
type CreateServerRequest = paths["/server"]["post"]["requestBody"]["content"]["application/json"]
type CreateServerResponse = paths["/server"]["post"]["responses"][200]
type DeleteServerResponse = paths["/server/{server_id}"]["delete"]["responses"]["200"]["content"]["application/json"]

const server = ref(null)
const serverId = ref("")

const body: CreateServerRequest = {
  name: "My Server"
}

async function createServer() {
  const response = await $fetch<CreateServerResponse>(`${api}/server`, {
  method: 'POST',
  body,
  })
  server.value = response
  serverId.value = response.id
}

async function deleteServer() {
  if (!serverId.value) return

  const response = await $fetch<DeleteServerResponse>(`${api}/server/${serverId.value}`, {
    method: 'DELETE',
  })
  server.value = response
  serverId.value = ""
}
</script>
