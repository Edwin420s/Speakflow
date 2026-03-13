import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { sendWhatsAppMessage } from '../services/whatsappService'

export default function WhatsAppPanel() {
  const [summary, setSummary] = useState('')
  const [showMessage, setShowMessage] = useState(false)
  const [isSending, setIsSending] = useState(false)

  useEffect(() => {
    // Listen for conversation analysis results
    const handleAnalysis = (event) => {
      const result = event.detail
      if (result.summary) {
        setSummary(result.summary)
        setShowMessage(true)
      }
    }

    window.addEventListener('conversation-analyzed', handleAnalysis)
    return () => window.removeEventListener('conversation-analyzed', handleAnalysis)
  }, [])

  const formatWhatsAppMessage = (summary, tasksCount) => {
    return `Hi team 👋

Here are the action items from today's meeting:

${summary}

📋 ${tasksCount} task(s) extracted and added to Trello

Let's keep the momentum 🚀`
  }

  const handleSendToWhatsApp = async () => {
    if (!summary) return
    
    setIsSending(true)
    try {
      const result = await sendWhatsAppMessage(summary)
      console.log('WhatsApp result:', result)
      alert('WhatsApp message sent successfully!')
    } catch (error) {
      console.error('Failed to send WhatsApp message:', error)
      alert('Failed to send WhatsApp message')
    } finally {
      setIsSending(false)
    }
  }

  const message = summary ? formatWhatsAppMessage(summary, 3) : ''

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">💬 WhatsApp Summary</h2>

      {showMessage && summary ? (
        <motion.pre
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
          className="bg-black/50 text-green-400 p-4 rounded text-sm whitespace-pre-wrap font-mono border border-gray-700"
        >
          {message}
        </motion.pre>
      ) : (
        <div className="flex items-center justify-center h-40 text-gray-500">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
          Generating summary...
        </div>
      )}

      <button
        onClick={handleSendToWhatsApp}
        disabled={!showMessage || !summary || isSending}
        className={`w-full mt-6 py-2 rounded transition ${
          showMessage && summary && !isSending
            ? 'bg-green-600 hover:bg-green-700'
            : 'bg-gray-700 cursor-not-allowed'
        }`}
      >
        {isSending ? 'Sending...' : 'Send to WhatsApp'}
      </button>
    </div>
  )
}