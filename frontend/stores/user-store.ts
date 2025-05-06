import type {paths} from "~/types/api";
type User = paths["/user/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"]

export const useUserStore = defineStore('user', () => {
    const currentUser = ref<User>(null)
    const authStore = useAuthStore()
    const runtimeConfig = useRuntimeConfig()

    async function fetchUser() {
        if (!authStore.currentlyLoggedInAuthUser) {
            await authStore.fetchAuthUser()
        }

        currentUser.value = await $fetch(`${runtimeConfig.public.apiBase}/user/${authStore.currentlyLoggedInAuthUser.id}`)
    }

    return {
        currentUser,
        fetchUser
    }
})
