// Travel Agent Pro - UI State Management
// 管理界面状态和交互

import { create } from 'zustand'

interface UIState {
  // 模态框状态
  isModalOpen: boolean
  isStyleDropdownOpen: boolean
  
  // 后端连接状态
  backendHealthy: boolean | null
  
  // 表单状态
  selectedStyle: string
  tags: Array<{ id: number; text: string; type: 'system' | 'custom' }>
  tagInput: string
  specialRequirement: string
  
  // 模态框操作
  openModal: () => void
  closeModal: () => void
  
  // 下拉框操作
  openStyleDropdown: () => void
  closeStyleDropdown: () => void
  toggleStyleDropdown: () => void
  
  // 后端状态
  setBackendHealthy: (healthy: boolean | null) => void
  
  // 表单操作
  setSelectedStyle: (style: string) => void
  addTag: (text: string) => void
  removeTag: (id: number) => void
  setTagInput: (input: string) => void
  setSpecialRequirement: (requirement: string) => void
  resetForm: () => void
}

const defaultTags = [
  { id: 1, text: '亲子', type: 'system' as const },
  { id: 2, text: '避免博物馆', type: 'custom' as const }
]

export const useUIStore = create<UIState>((set, get) => ({
  // 初始状态
  isModalOpen: false,
  isStyleDropdownOpen: false,
  backendHealthy: null,
  selectedStyle: 'relaxed',
  tags: defaultTags,
  tagInput: '',
  specialRequirement: '',
  
  // 模态框操作
  openModal: () => set({ isModalOpen: true }),
  closeModal: () => set({ isModalOpen: false, isStyleDropdownOpen: false }),
  
  // 下拉框操作
  openStyleDropdown: () => set({ isStyleDropdownOpen: true }),
  closeStyleDropdown: () => set({ isStyleDropdownOpen: false }),
  toggleStyleDropdown: () => set(state => ({ 
    isStyleDropdownOpen: !state.isStyleDropdownOpen 
  })),
  
  // 后端状态
  setBackendHealthy: (healthy: boolean | null) => set({ backendHealthy: healthy }),
  
  // 表单操作
  setSelectedStyle: (style: string) => set({ 
    selectedStyle: style,
    isStyleDropdownOpen: false 
  }),
  
  addTag: (text: string) => {
    const { tags } = get()
    const newTag = {
      id: Date.now(),
      text: text.trim(),
      type: 'custom' as const
    }
    set({ tags: [...tags, newTag], tagInput: '' })
  },
  
  removeTag: (id: number) => {
    const { tags } = get()
    set({ tags: tags.filter(tag => tag.id !== id) })
  },
  
  setTagInput: (input: string) => set({ tagInput: input }),
  
  setSpecialRequirement: (requirement: string) => set({ 
    specialRequirement: requirement 
  }),
  
  resetForm: () => set({
    selectedStyle: 'relaxed',
    tags: defaultTags,
    tagInput: '',
    specialRequirement: ''
  })
}))

// 便捷的选择器函数 - 使用稳定的引用避免无限渲染
export const useModal = () => ({
  isOpen: useUIStore(state => state.isModalOpen),
  open: useUIStore(state => state.openModal),
  close: useUIStore(state => state.closeModal)
})

export const useStyleDropdown = () => ({
  isOpen: useUIStore(state => state.isStyleDropdownOpen),
  selectedStyle: useUIStore(state => state.selectedStyle),
  toggle: useUIStore(state => state.toggleStyleDropdown),
  close: useUIStore(state => state.closeStyleDropdown),
  setStyle: useUIStore(state => state.setSelectedStyle)
})

export const useFormState = () => ({
  tags: useUIStore(state => state.tags),
  tagInput: useUIStore(state => state.tagInput),
  specialRequirement: useUIStore(state => state.specialRequirement),
  addTag: useUIStore(state => state.addTag),
  removeTag: useUIStore(state => state.removeTag),
  setTagInput: useUIStore(state => state.setTagInput),
  setSpecialRequirement: useUIStore(state => state.setSpecialRequirement),
  reset: useUIStore(state => state.resetForm)
})
