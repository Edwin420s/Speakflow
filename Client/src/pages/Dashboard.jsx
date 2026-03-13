import { motion } from 'framer-motion'
import ConversationPanel from '../components/ConversationPanel'
import TaskPanel from '../components/TaskPanel'
import WhatsAppPanel from '../components/WhatsAppPanel'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-[#0B1120] text-white p-6 md:p-10">
      <h1 className="text-3xl font-bold mb-10 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
        SpeakFlow AI Dashboard
      </h1>

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
    </div>
  )
}