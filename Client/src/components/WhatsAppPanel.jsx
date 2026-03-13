import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function WhatsAppPanel() {
  const [showMessage, setShowMessage] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setShowMessage(true), 7000)
    return () => clearTimeout(timer)
  }, [])

  const message = `Hi team 👋

Here are the action items from today's meeting:

• Edwin – Finish backend tonight
• Sarah – Design UI by Friday
• John – Send proposal tomorrow

Let's keep the momentum 🚀`

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">💬 WhatsApp Summary</h2>

      {showMessage ? (
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
        className={`w-full mt-6 py-2 rounded transition ${
          showMessage
            ? 'bg-green-600 hover:bg-green-700'
            : 'bg-gray-700 cursor-not-allowed'
        }`}
        disabled={!showMessage}
      >
        Send to WhatsApp
      </button>
    </div>
  )
}