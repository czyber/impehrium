import { defineNuxtPlugin, useRuntimeConfig } from '#imports'
import { client } from '~/src/client/client.gen'            // wherever your generated client is
import { createClientConfig } from '~/src/heyapi-client-config'

export default defineNuxtPlugin(() => {
  const { public: { apiBase } } = useRuntimeConfig()

  // re-create or re-configure the client so baseURL is correct at runtime
  const cfg = createClientConfig({ baseURL: apiBase })
  client.setConfig(cfg)

  // Optionally, make it injectable via `useNuxtApp().$heyapi`, etc.
  return {
    provide: {
      heyapi: client
    }
  }
})
