import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ConversationPanel() {
  const [messages, setMessages] = useState([])

  useEffect(() => {
    const simulatedConversation = [
      "John: Action item — Edwin finish backend tonight",
      "Sarah: Reminder — Send proposal tomorrow",
      "John: Follow-up — Send summary to the team",
      "Edwin: I'll have it done by 8pm",
      "Sarah: Great, let's review on Thursday"
    ]

    let i = 0
    const interval = setInterval(() => {
      if (i < simulatedConversation.length) {
        setMessages(prev => [...prev, simulatedConversation[i]])
        i++
      } else {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
        Live Conversation
      </h2>

      <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-black/50 p-3 rounded border border-gray-700 text-sm"
            >
              {msg}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="mt-4 flex items-center text-sm text-gray-400">
        <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
        AI is listening...
      </div>
    </div>
  )
}