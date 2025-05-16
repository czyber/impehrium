
export const useHomeworkAssistantStore = defineStore("homework-assistant", () => {
    const fileUploaded = ref<Boolean>(false)
    const selectedFile = ref<File|null>(null)

    return {
        fileUploaded,
        selectedFile
    }
})
