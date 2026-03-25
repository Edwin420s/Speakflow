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

  const getPriorityColor = (priority) => {
    const colors = {
      'urgent': 'bg-red-500',
      'high': 'bg-orange-500', 
      'medium': 'bg-yellow-500',
      'low': 'bg-green-500'
    }
    return colors[priority] || 'bg-gray-500'
  }

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-gray-500',
      'in_progress': 'bg-blue-500',
      'completed': 'bg-green-500',
      'cancelled': 'bg-red-500'
    }
    return colors[status] || 'bg-gray-500'
  }

  const getStatusIcon = (status) => {
    const icons = {
      'pending': '⏳',
      'in_progress': '🔄', 
      'completed': '✅',
      'cancelled': '❌'
    }
    return icons[status] || '⏳'
  }

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
                <div className="flex items-center justify-between text-sm text-gray-400 mt-1">
                  <span>👤 {t.assigned_to || 'Unassigned'}</span>
                  <span>⏳ {t.deadline || 'No deadline'}</span>
                </div>
                
                {/* Priority and Status Badges */}
                <div className="flex items-center gap-2 mt-2">
                  <span className={`px-2 py-1 rounded-full text-xs text-white ${getPriorityColor(t.priority)}`}>
                    {t.priority || 'medium'}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs text-white flex items-center gap-1 ${getStatusColor(t.status)}`}>
                    {getStatusIcon(t.status)} {t.status || 'pending'}
                  </span>
                </div>
                
                {/* Tags */}
                {t.tags && t.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {t.tags.map((tag, tagIndex) => (
                      <span key={tagIndex} className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Estimated Time */}
                {t.estimated_time && (
                  <div className="text-xs text-gray-400 mt-1">
                    ⏱️ Estimated: {t.estimated_time}
                  </div>
                )}
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