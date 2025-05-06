import {defineStore} from "pinia";
import type {User} from "@supabase/auth-js";
import type {paths} from "~/types/api";

type User = paths["/user"]["get"]

export const useAuthStore = defineStore('auth', () => {
    const currentlyLoggedInAuthUser = ref<User>(null)

    async function fetchAuthUser() {
        const { data } = await useSupabaseClient().auth.getUser()
        currentlyLoggedInAuthUser.value = data?.user
    }

    return {
        currentlyLoggedInAuthUser,
        fetchAuthUser
    }
})
