import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    }
  },

  css: ['~/assets/css/tailwind.css'],

  vite: {
    plugins: [
      tailwindcss(),
    ],
  },

  modules: ['@pinia/nuxt', 'shadcn-nuxt', '@nuxtjs/supabase', 'nuxt-lucide-icons', '@nuxtjs/i18n'],
  shadcn: {
    prefix: '',
    componentDir: './components/ui'
  },
  i18n: {
    defaultLocale: 'en',
    locales: [
      { code: 'en', name: 'English', file: 'en.json' },
      { code: 'ger', name: 'German', file: 'ger.json' }
    ]
  }
})
