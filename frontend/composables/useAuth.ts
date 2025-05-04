import { ref, onMounted } from 'vue'
import { useRouter }      from 'vue-router'

export function useAuth() {
    const user     = ref(null)
    const supabase = useSupabaseClient()
    const router   = useRouter()

    onMounted(async () => {
        const { data } = await supabase.auth.getSession()
        user.value = data.session?.user ?? null
    })
    user.value = supabase.auth.getUser() || null

    const signIn = async (email: string, password: string) => {
        console.log(email)
        console.log(password)
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
        navigateTo('/welcome')
    }

    const signOut = async () => {
        const { error } = await supabase.auth.signOut()
        navigateTo('/login')
    }

    return { user, signIn, signOut }
}
