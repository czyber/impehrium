<script setup lang="ts">

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  type SidebarProps,
  SidebarRail,
} from '@/components/ui/sidebar'
import {LightbulbIcon, LucideMessageCircleQuestion, UploadIcon} from "lucide-vue-next";
import {useAuth} from "~/composables/useAuth";

const props = defineProps<SidebarProps>()

const {signOut} = useAuth()

const data = {
  versions: ['1.0.1', '1.1.0-alpha', '2.0.0-beta1'],
  navMain: [
    {
      title: 'General',
      url: '#',
      items: [
        {
          title: 'Ask a question',
          url: '#',
          icon: LightbulbIcon
        },
        {
          title: 'Upload Homework',
          url: '/homework-assistant',
          icon: UploadIcon
        },
      ],
    },
  ],
}
</script>

<template>
  <Sidebar v-bind="props">
    <SidebarHeader>
      <h1>Athena</h1>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup v-for="item in data.navMain" :key="item.title">
        <SidebarGroupLabel>{{ item.title }}</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="childItem in item.items" :key="childItem.title">
              <SidebarMenuButton :is-active="childItem.isActive">
                <component :is="childItem.icon" v-if="childItem.icon" />
                <a :href="childItem.url">{{ childItem.title }}</a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarRail />
    <SidebarFooter>
      <SidebarContent>
        <SidebarMenuButton class="hover:cursor-pointer" @click="signOut">
          <LucideLogOut/>
          Sign out
        </SidebarMenuButton>
      </SidebarContent>
    </SidebarFooter>
  </Sidebar>
</template>
