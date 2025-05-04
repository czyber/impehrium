<template>
  <SidebarProvider>
    <AppSidebar/>
    <main>
      <SidebarTrigger />
      <slot />
    </main>
  </SidebarProvider>
  <div class="min-h-screen flex flex-col">
    <main class="flex-1 p-6">
      <slot />
    </main>

    <footer class="bg-gray-100 text-gray-600 p-4 text-center">
      © 2025 My App
    </footer>
  </div>
</template>
<script setup lang="ts">
</script>
