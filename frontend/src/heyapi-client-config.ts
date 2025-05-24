import type { CreateClientConfig as CC } from './client/client.gen'
import { createConfig, type Config, type ClientOptions as DefaultClientOptions } from '@hey-api/client-axios'

export const createClientConfig: CC = (override?: Config<DefaultClientOptions>) => {
  // the plugin will pass { baseURL: apiBase } here
  return {
    ...createConfig<DefaultClientOptions>(),
    ...override,
  }
}
