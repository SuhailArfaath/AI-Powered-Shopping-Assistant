import { create } from 'zustand'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  inboundGuardrails?: { name: string; passed: boolean }[]
  outboundGuardrails?: { name: string; passed: boolean }[]
  guardrailHit?: string | null
  showOrderButton?: boolean
}

interface ChatState {
  messages: ChatMessage[]
  isOpen: boolean
  isTyping: boolean
  sessionId: string
  addMessage: (message: ChatMessage) => void
  setTyping: (typing: boolean) => void
  toggleOpen: () => void
  setOpen: (open: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! Welcome to **AI Shopping Cart**! 😊\n\nI can help you:\n• 🔍 **Search for products** — Just tell me what you\'re looking for!\n• 🛒 **Place orders** — Choose a product and I\'ll guide you\n• 📦 **Check order status** — Provide your order ID or email\n\nHow can I assist you today?',
      timestamp: new Date(),
    },
  ],
  isOpen: true,
  isTyping: false,
  sessionId: 'session-' + Math.random().toString(36).substring(2, 10),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setTyping: (typing) => set({ isTyping: typing }),
  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (open) => set({ isOpen: open }),
  clearMessages: () => set({ messages: [] }),
}))