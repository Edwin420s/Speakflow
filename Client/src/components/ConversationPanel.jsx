import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { analyzeConversation, connectOmiDevice, getOmiStatus, startDemoStream } from '../services/api'

export default function ConversationPanel() {
  const [messages, setMessages] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcriptText, setTranscriptText] = useState('')
  const [omiConnected, setOmiConnected] = useState(false)
  const [demoMode, setDemoMode] = useState('kenyan') // 'kenyan', 'tech', 'default'

  const kenyanBusinessConversation = [
    "Edwin: Team, let's discuss our fintech app for the Kenyan market. We need proper M-Pesa integration.",
    "Sarah: I'll handle the UI design for the mobile app. I can have the mockups ready by next week.",
    "John: I should contact KCB and Equity Bank about partnership discussions. Let me schedule that for Tuesday.",
    "Mary: We need to finalize the API documentation for the developers. Edwin, can you get that done by Friday?",
    "Edwin: Sure, I'll complete the API docs by Friday. Also, someone needs to register the company name.",
    "John: I'll take care of the business registration next month after we secure funding.",
    "Sarah: Don't forget we need to test the app on Safaricom's network before launch.",
    "Mary: Right, I'll coordinate with the Safaricom developer team for testing access."
  ]

  const techStartupConversation = [
    "Alex: We need to deploy the new version of our platform tonight.",
    "Jamie: I'll handle the backend deployment and database migration.",
    "Taylor: Can someone update the documentation after deployment?",
    "Alex: Jamie, please focus on the API endpoints first.",
    "Jamie: Got it. I'll start with the user authentication endpoints.",
    "Taylor: I'll prepare the deployment checklist and monitor the servers."
  ]

  const getConversation = () => {
    switch (demoMode) {
      case 'kenyan':
        return kenyanBusinessConversation
      case 'tech':
        return techStartupConversation
      default:
        return kenyanBusinessConversation
    }
  }

  useEffect(() => {
    // Check Omi device status on component mount
    checkOmiStatus()
  }, [])

  const checkOmiStatus = async () => {
    try {
      const status = await getOmiStatus()
      setOmiConnected(status.device_connected)
    } catch (error) {
      console.error('Failed to check Omi status:', error)
    }
  }

  const handleConnectOmi = async () => {
    try {
      await connectOmiDevice()
      setOmiConnected(true)
    } catch (error) {
      console.error('Failed to connect Omi device:', error)
    }
  }

  const handleStartDemoStream = async () => {
    setIsProcessing(true)
    try {
      const result = await startDemoStream()
      // Update messages with demo stream results
      setMessages(prev => [...prev, `🎤 Omi Device: Demo stream started - ${result.tasks_extracted} tasks extracted`])
      
      // Emit event to update other panels
      window.dispatchEvent(new CustomEvent('conversation-analyzed', { 
        detail: {
          tasks: result.demo_tasks || [],
          summary: `Demo stream completed with ${result.tasks_extracted} tasks extracted from Omi device conversation.`
        }
      }))
    } catch (error) {
      console.error('Demo stream failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  useEffect(() => {
    let i = 0
    let currentTranscript = ''
    const conversation = getConversation()
    
    const interval = setInterval(() => {
      if (i < conversation.length) {
        const newMessage = conversation[i]
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
  }, [demoMode])

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
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500 animate-pulse'}`}></span>
          Live Conversation
          {omiConnected && <span className="text-xs bg-green-600 px-2 py-1 rounded">🎤 Omi Connected</span>}
        </h2>
        
        <div className="flex items-center gap-2">
          <select
            value={demoMode}
            onChange={(e) => setDemoMode(e.target.value)}
            className="bg-gray-700 text-white text-sm px-2 py-1 rounded border border-gray-600"
          >
            <option value="kenyan">🇰🇪 Kenyan Business</option>
            <option value="tech">💻 Tech Startup</option>
            <option value="default">📝 Default</option>
          </select>
        </div>
      </div>

      {/* Omi Device Controls */}
      <div className="mb-4 p-3 bg-black/30 rounded border border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">🎤 Omi AI Wearable</span>
          <span className={`text-xs px-2 py-1 rounded ${omiConnected ? 'bg-green-600' : 'bg-gray-600'}`}>
            {omiConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex gap-2">
          {!omiConnected ? (
            <button
              onClick={handleConnectOmi}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition"
            >
              Connect Omi Device
            </button>
          ) : (
            <button
              onClick={handleStartDemoStream}
              disabled={isProcessing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-3 py-1 rounded text-sm transition"
            >
              {isProcessing ? 'Streaming...' : 'Start Demo Stream'}
            </button>
          )}
        </div>
      </div>

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
          <div className={`w-2 h-2 rounded-full mr-2 ${isProcessing ? 'bg-yellow-500' : 'bg-blue-500'}`}></div>
          {isProcessing ? 'AI analyzing...' : omiConnected ? '🎤 Omi is listening...' : 'AI is listening...'}
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