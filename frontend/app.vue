<template>
  <NuxtLayout>
    <NuxtPage/>
  </NuxtLayout>
</template>

<script setup lang="ts">
import type { paths } from '~/types/api'
import {Button} from "~/components/ui/button";

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
