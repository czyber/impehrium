import { useNuxtApp } from '#app'

export function useUsers() {
  const { $api } = useNuxtApp()
  return {
    //list: () => $api('/user'),
    get: (id: string) => $api(`/user/${id}`),
    create: (body: { name: string }) => $api.post('/user', { body })
  }
}
