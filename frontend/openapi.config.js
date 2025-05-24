import { defineConfig, defaultPlugins } from '@hey-api/openapi-ts'

export default defineConfig({
  input:  './openapi.json',    // ← now a file, not http://…
  output: './src/client',
  plugins: [
    // bring in the built-in TS + SDK plugins…
    ...defaultPlugins,

    // …then your HTTP client
    {
      name:            '@hey-api/client-axios',
      runtimeConfigPath: './src/heyapi-client-config.ts',
    },

    // and override the SDK to be generated as classes
    {
      name:    '@hey-api/sdk',
      asClass: true,
    },
  ],
})
