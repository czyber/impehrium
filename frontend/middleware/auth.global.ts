import { defineNuxtRouteMiddleware, navigateTo } from '#imports'
import { useAuth } from '~/composables/useAuth'

export default defineNuxtRouteMiddleware((to) => {
  const { user } = useAuth()
  if (to.path !== '/login' && !user.value) {
    return navigateTo('/login')
  }
})
