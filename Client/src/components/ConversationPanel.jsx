import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { analyzeConversation } from '../services/api'

export default function ConversationPanel() {
  const [messages, setMessages] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcriptText, setTranscriptText] = useState('')

  const simulatedConversation = [
    "John: Action item — Edwin finish backend tonight",
    "Sarah: Reminder — Send proposal tomorrow",
    "John: Follow-up — Send summary to the team",
    "Edwin: I'll have it done by 8pm",
    "Sarah: Great, let's review on Thursday"
  ]

  useEffect(() => {
    let i = 0
    let currentTranscript = ''
    const interval = setInterval(() => {
      if (i < simulatedConversation.length) {
        const newMessage = simulatedConversation[i]
        setMessages(prev => [...prev, newMessage])
        currentTranscript += newMessage + '\n'
        setTranscriptText(currentTranscript)
        i++
      } else {
        clearInterval(interval)
        // Auto-process when conversation ends
        if (currentTranscript) {
          handleAnalyze(currentTranscript)
        }
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const handleAnalyze = async (text) => {
    if (!text || !text.trim()) return
    
    setIsProcessing(true)
    try {
      const result = await analyzeConversation(text)
      // Emit event to update other panels
      window.dispatchEvent(new CustomEvent('conversation-analyzed', { 
        detail: result 
      }))
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500 animate-pulse'}`}></span>
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

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center text-sm text-gray-400">
          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
          {isProcessing ? 'AI analyzing...' : 'AI is listening...'}
        </div>
        
        {transcriptText && !isProcessing && (
          <button
            onClick={() => handleAnalyze(transcriptText)}
            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition"
          >
            Analyze
          </button>
        )}
      </div>
    </div>
  )
}