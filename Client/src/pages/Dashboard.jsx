import { useState } from 'react'
import { motion } from 'framer-motion'
import ConversationPanel from '../components/ConversationPanel'
import TaskPanel from '../components/TaskPanel'
import WhatsAppPanel from '../components/WhatsAppPanel'
import ActivityFeed from '../components/ActivityFeed'
import Timeline from '../components/Timeline'

export default function Dashboard() {
  const [viewMode, setViewMode] = useState('classic') // 'classic' or 'enhanced'

  return (
    <div className="min-h-screen bg-[#0B1120] text-white p-6 md:p-10">
      <div className="flex items-center justify-between mb-10">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          SpeakFlow AI Dashboard
        </h1>
        
        {/* View Toggle */}
        <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('classic')}
            className={`px-4 py-2 rounded text-sm transition ${
              viewMode === 'classic' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Classic View
          </button>
          <button
            onClick={() => setViewMode('enhanced')}
            className={`px-4 py-2 rounded text-sm transition ${
              viewMode === 'enhanced' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Enhanced View
          </button>
        </div>
      </div>

      {/* Classic View - Original 3-panel layout */}
      {viewMode === 'classic' && (
        <div className="grid md:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <ConversationPanel />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <TaskPanel />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <WhatsAppPanel />
          </motion.div>
        </div>
      )}

      {/* Enhanced View - New layout with Activity Feed and Timeline */}
      {viewMode === 'enhanced' && (
        <div className="space-y-8">
          {/* Top Row - Conversation and Tasks */}
          <div className="grid md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <ConversationPanel />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <TaskPanel />
            </motion.div>
          </div>

          {/* Middle Row - Timeline and WhatsApp */}
          <div className="grid md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Timeline />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <WhatsAppPanel />
            </motion.div>
          </div>

          {/* Bottom Row - Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <ActivityFeed />
          </motion.div>
        </div>
      )}
    </div>
  )
}