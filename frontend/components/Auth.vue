<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from "~/composables/useAuth"

const { signIn } = useAuth()

const email = ref<string>("")
const password = ref<string>("")

</script>

<template>
  <Card class="w-full max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">
        Login
      </CardTitle>
      <CardDescription>
        Enter your email below to login to your account.
      </CardDescription>
    </CardHeader>
    <CardContent class="grid gap-4">
      <div class="grid gap-2">
        <Label for="email">Email</Label>
        <Input v-model="email" id="email" type="email" placeholder="m@example.com" required />
      </div>
      <div class="grid gap-2">
        <Label for="password">Password</Label>
        <Input v-model="password" id="password" type="password" required />
      </div>
    </CardContent>
    <CardFooter>
      <Button class="w-full" @click="signIn(email, password)">
        Sign in
      </Button>
    </CardFooter>
  </Card>
</template>
