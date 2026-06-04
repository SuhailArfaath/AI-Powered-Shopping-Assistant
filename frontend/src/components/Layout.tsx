import { ReactNode } from 'react'
import Navbar from './Navbar'
import ChatPanel from './ChatPanel'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen w-full bg-gray-50">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
      
      {/* Fixed Chat Panel - Right Side */}
      <ChatPanel />
    </div>
  )
}