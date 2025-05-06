import { Fetch } from 'ofetch'

declare module '#app' {
  interface NuxtApp {
    $api: ReturnType<typeof Fetch>
  }
}
