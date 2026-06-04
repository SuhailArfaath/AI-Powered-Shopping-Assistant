import { useState, useRef, useEffect } from 'react'
import { X, Send, ChevronLeft, Bot, User, AlertTriangle, Shield, ShieldCheck } from 'lucide-react'
import { useChatStore, ChatMessage } from '../store/chatStore'
import { api } from '../api/client'

function GuardrailBadge({ name, passed }: { name: string; passed: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${
        passed
          ? 'bg-green-100 text-green-700 border border-green-200'
          : 'bg-red-100 text-red-700 border border-red-200 animate-pulse'
      }`}
    >
      {passed ? (
        <ShieldCheck size={10} />
      ) : (
        <Shield size={10} />
      )}
      {name.replace(/_/g, ' ')}
    </span>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  const isGuardrailHit = message.guardrailHit
  const hasGuardrails = message.inboundGuardrails && message.outboundGuardrails

  return (
    <div className={`flex gap-2 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-blue-600' : 'bg-emerald-500'
        }`}
      >
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
      </div>

      {/* Message */}
      <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Guardrail Labels - always shown */}
        {hasGuardrails && (
          <div className="flex flex-wrap gap-1 mb-1">
            {message.inboundGuardrails!.map((g) => (
              <GuardrailBadge key={`in-${g.name}`} name={g.name} passed={g.passed} />
            ))}
            <span className="text-gray-300 mx-0.5">|</span>
            {message.outboundGuardrails!.map((g) => (
              <GuardrailBadge key={`out-${g.name}`} name={g.name} passed={g.passed} />
            ))}
          </div>
        )}

        {/* Content */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-md'
              : isGuardrailHit
              ? 'bg-red-50 text-red-800 border border-red-200 rounded-tl-md'
              : 'bg-white text-gray-800 border border-gray-200 rounded-tl-md shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="text-sm whitespace-pre-wrap">
              {message.content}
            </div>
          )}
        </div>

        {/* Place Order + Cancel Buttons */}
        {message.showOrderButton && (
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={() => window.dispatchEvent(new CustomEvent('place-order-confirm'))}
              className="flex-1 bg-green-600 text-white py-3 px-4 rounded-xl font-bold text-sm hover:bg-green-700 active:bg-green-800 transition-all shadow-md cursor-pointer flex items-center justify-center gap-2"
            >
              ✅ Place Order
            </button>
            <button
              type="button"
              onClick={() => window.dispatchEvent(new CustomEvent('place-order-cancel'))}
              className="flex-1 bg-red-500 text-white py-3 px-4 rounded-xl font-bold text-sm hover:bg-red-600 active:bg-red-700 transition-all shadow-md cursor-pointer flex items-center justify-center gap-2"
            >
              ❌ Cancel
            </button>
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-[10px] text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const { messages, isOpen, isTyping, sessionId, addMessage, setTyping, setOpen, toggleOpen } = useChatStore()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  // Listen for Place Order button clicks
  useEffect(() => {
    const handler = () => {
      setTyping(true)
      // Add user's confirm message
      addMessage({
        id: `user-${Date.now()}`,
        role: 'user',
        content: 'confirm order',
        timestamp: new Date(),
      })
      // Send confirm order to backend
      api.sendChat({ message: 'confirm order', sessionId }).then((response) => {
        addMessage({
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: response.reply,
          timestamp: new Date(),
          inboundGuardrails: response.inbound_guardrails,
          outboundGuardrails: response.outbound_guardrails,
          guardrailHit: response.inbound_guardrails.some(g => !g.passed)
            ? response.inbound_guardrails.find(g => !g.passed)?.name
            : response.outbound_guardrails.some(g => !g.passed)
            ? response.outbound_guardrails.find(g => !g.passed)?.name
            : null,
        })
      }).catch(() => {
        addMessage({
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ Sorry, there was an error placing your order. Please try again.',
          timestamp: new Date(),
        })
      }).finally(() => {
        setTyping(false)
      })
    }
    window.addEventListener('place-order-confirm', handler)
    return () => window.removeEventListener('place-order-confirm', handler)
  }, [sessionId])

  // Listen for Cancel button clicks
  useEffect(() => {
    const cancelHandler = () => {
      setTyping(true)
      addMessage({
        id: `user-${Date.now()}`,
        role: 'user',
        content: 'cancel',
        timestamp: new Date(),
      })
      api.sendChat({ message: 'cancel', sessionId }).then((response) => {
        addMessage({
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: response.reply,
          timestamp: new Date(),
          inboundGuardrails: response.inbound_guardrails,
          outboundGuardrails: response.outbound_guardrails,
        })
      }).catch(() => {
        addMessage({
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ Sorry, there was an error cancelling the order. Please try again.',
          timestamp: new Date(),
        })
      }).finally(() => {
        setTyping(false)
      })
    }
    window.addEventListener('place-order-cancel', cancelHandler)
    return () => window.removeEventListener('place-order-cancel', cancelHandler)
  }, [sessionId])

  const handleSend = async () => {
    const text = input.trim()
    if (!text) return
    setInput('')

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    addMessage(userMsg)
    setTyping(true)

    try {
      const response = await api.sendChat({ message: text, sessionId })

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        timestamp: new Date(),
        inboundGuardrails: response.inbound_guardrails,
        outboundGuardrails: response.outbound_guardrails,
        guardrailHit: response.inbound_guardrails.some(g => !g.passed) 
          ? response.inbound_guardrails.find(g => !g.passed)?.name 
          : response.outbound_guardrails.some(g => !g.passed)
          ? response.outbound_guardrails.find(g => !g.passed)?.name
          : null,
        showOrderButton: response.show_order_button,
      }
      addMessage(aiMsg)
    } catch (err) {
      addMessage({
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: '⚠️ Sorry, I encountered an error connecting to the server. Please try again.',
        timestamp: new Date(),
      })
    } finally {
      setTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={toggleOpen}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-all z-50"
        title="Open AI Chat"
      >
        <Bot size={24} />
      </button>
    )
  }

  return (
    <div className="w-[420px] min-w-[420px] bg-white border-l border-gray-200 flex flex-col shadow-lg z-40">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={20} />
          <div>
            <h3 className="font-semibold text-sm">AI Shopping Assistant</h3>
            <p className="text-[10px] text-blue-200">Powered by LangGraph + GPT-4o</p>
          </div>
        </div>
        <button
          onClick={toggleOpen}
          className="p-1 hover:bg-blue-500 rounded transition-colors"
          title="Close chat"
        >
          <ChevronLeft size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isTyping && (
          <div className="flex gap-2 mb-4">
            <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
              <Bot size={16} className="text-white" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-3 bg-white">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about products, orders..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isTyping}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}