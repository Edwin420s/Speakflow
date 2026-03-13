import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { createTrelloCard } from '../services/trelloService'

export default function TaskPanel() {
  const [tasks, setTasks] = useState([])
  const [isSending, setIsSending] = useState(false)

  useEffect(() => {
    // Listen for conversation analysis results
    const handleAnalysis = (event) => {
      const result = event.detail
      if (result.tasks && result.tasks.length > 0) {
        setTasks(result.tasks)
      }
    }

    window.addEventListener('conversation-analyzed', handleAnalysis)
    return () => window.removeEventListener('conversation-analyzed', handleAnalysis)
  }, [])

  const handleSendToTrello = async () => {
    if (tasks.length === 0) return
    
    setIsSending(true)
    try {
      // Send each task to Trello
      const results = await Promise.all(
        tasks.map(task => createTrelloCard(task))
      )
      
      console.log('Trello results:', results)
      
      // Show success feedback
      const successCount = results.filter(r => r.success).length
      alert(`Successfully created ${successCount} Trello cards!`)
    } catch (error) {
      console.error('Failed to send to Trello:', error)
      alert('Failed to send some tasks to Trello')
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">📋 Generated Tasks</h2>

      <div className="space-y-3 min-h-[200px]">
        <AnimatePresence>
          {tasks.map((t, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="bg-black/50 p-4 rounded border border-gray-700"
            >
              <p className="font-medium">{t.task}</p>
              <div className="flex justify-between text-sm text-gray-400 mt-1">
                <span>👤 {t.assigned_to || 'Unassigned'}</span>
                <span>⏳ {t.deadline || 'No deadline'}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {tasks.length === 0 && (
          <div className="text-gray-500 text-center py-8">
            Waiting for conversation analysis...
          </div>
        )}
      </div>

      <button
        onClick={handleSendToTrello}
        disabled={tasks.length === 0 || isSending}
        className={`w-full mt-6 py-2 rounded transition ${
          tasks.length === 0 || isSending
            ? 'bg-gray-700 cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {isSending ? 'Sending to Trello...' : 'Send to Trello'}
      </button>
    </div>
  )
}