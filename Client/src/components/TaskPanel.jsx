import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function TaskPanel() {
  const [tasks, setTasks] = useState([])

  useEffect(() => {
    const simulatedTasks = [
      { task: 'Finish backend API', person: 'Edwin', deadline: 'tonight' },
      { task: 'Design UI mockups', person: 'Sarah', deadline: 'Friday' },
      { task: 'Send proposal to client', person: 'John', deadline: 'tomorrow' }
    ]

    let i = 0
    const interval = setInterval(() => {
      if (i < simulatedTasks.length) {
        setTasks(prev => [...prev, simulatedTasks[i]])
        i++
      } else {
        clearInterval(interval)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [])

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
                <span>👤 {t.person}</span>
                <span>⏳ {t.deadline}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <button className="w-full mt-6 bg-green-600 hover:bg-green-700 py-2 rounded transition">
        Send to Trello
      </button>
    </div>
  )
}