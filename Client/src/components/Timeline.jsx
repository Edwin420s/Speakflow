import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getTimeline, createTimelineEvent, updateTimelineEvent, getActivityTypeIcon, getActivityTypeLabel } from '../services/activityService'

export default function Timeline() {
  const [timeline, setTimeline] = useState({ events: [], total_events: 0, completion_percentage: 0 })
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newEvent, setNewEvent] = useState({ title: '', description: '', event_type: 'task_created' })

  useEffect(() => {
    fetchTimeline()
  }, [filter])

  const fetchTimeline = async () => {
    try {
      setLoading(true)
      const filters = filter ? { event_type: filter } : {}
      const data = await getTimeline(filters)
      setTimeline(data)
    } catch (error) {
      console.error('Failed to fetch timeline:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateEvent = async () => {
    if (!newEvent.title || !newEvent.description) return

    try {
      await createTimelineEvent(newEvent)
      setNewEvent({ title: '', description: '', event_type: 'task_created' })
      setShowCreateForm(false)
      fetchTimeline() // Refresh timeline
    } catch (error) {
      console.error('Failed to create event:', error)
    }
  }

  const handleUpdateEvent = async (eventId, updates) => {
    try {
      await updateTimelineEvent(eventId, updates)
      fetchTimeline() // Refresh timeline
    } catch (error) {
      console.error('Failed to update event:', error)
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getProgressColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500'
    if (percentage >= 50) return 'bg-yellow-500'
    if (percentage >= 20) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getEventIcon = (eventType) => {
    return getActivityTypeIcon(eventType) || '📄'
  }

  const getEventTypeColor = (eventType) => {
    const colors = {
      'task_created': 'blue',
      'task_completed': 'green',
      'task_assigned': 'purple',
      'transcript_processed': 'yellow',
      'trello_card_created': 'orange',
      'whatsapp_sent': 'teal',
      'omi_device_connected': 'indigo',
      'omi_conversation_processed': 'pink',
      'ai_processing_started': 'gray',
      'ai_processing_completed': 'emerald'
    }
    return colors[eventType] || 'gray'
  }

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          Timeline Progress
          <span className="text-sm text-gray-400">({timeline.total_events} events)</span>
        </h2>
        
        <div className="flex items-center gap-3">
          {/* Progress Overview */}
          <div className="text-sm text-gray-400">
            {timeline.completion_percentage.toFixed(0)}% Complete
          </div>
          
          {/* Filter dropdown */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600"
          >
            <option value="">All Events</option>
            <option value="task_created">Tasks</option>
            <option value="ai_processing_completed">AI Processing</option>
            <option value="trello_card_created">Trello</option>
            <option value="whatsapp_sent">WhatsApp</option>
            <option value="omi_conversation_processed">Omi Device</option>
          </select>
          
          {/* Add Event Button */}
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition"
          >
            + Add Event
          </button>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="mb-6 space-y-3">
        {/* Main Progress Bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-700 rounded-full h-3 overflow-hidden">
            <motion.div
              className={`h-full ${getProgressColor(timeline.completion_percentage)}`}
              initial={{ width: 0 }}
              animate={{ width: `${timeline.completion_percentage}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
          <span className="text-sm font-medium text-white">
            {timeline.completion_percentage.toFixed(1)}%
          </span>
        </div>
        
        {/* Task Statistics */}
        <div className="flex justify-between text-sm text-gray-400">
          <span>🟢 Active Tasks: {timeline.active_tasks}</span>
          <span>✅ Completed Tasks: {timeline.completed_tasks}</span>
          <span>📅 Timeline: {timeline.events.length > 0 ? `${timeline.events.length} events` : 'No events'}</span>
        </div>
      </div>

      {/* Create Event Form */}
      <AnimatePresence>
        {showCreateForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 bg-black/50 rounded-lg border border-gray-700"
          >
            <h3 className="text-lg font-medium mb-3">Create New Event</h3>
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Event title"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
              />
              <textarea
                placeholder="Event description"
                value={newEvent.description}
                onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 h-20 resize-none"
              />
              <select
                value={newEvent.event_type}
                onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
              >
                <option value="task_created">Task Created</option>
                <option value="task_completed">Task Completed</option>
                <option value="ai_processing_started">AI Processing Started</option>
                <option value="ai_processing_completed">AI Processing Completed</option>
                <option value="trello_card_created">Trello Card Created</option>
                <option value="whatsapp_sent">WhatsApp Sent</option>
                <option value="omi_device_connected">Omi Device Connected</option>
              </select>
              <div className="flex gap-2">
                <button
                  onClick={handleCreateEvent}
                  disabled={!newEvent.title || !newEvent.description}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded text-sm transition"
                >
                  Create Event
                </button>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded text-sm transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Timeline Events */}
      <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
            Loading timeline...
          </div>
        ) : timeline.events.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📅</div>
            <p>No timeline events yet</p>
            <p className="text-sm">Add events to track progress</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-600"></div>
            
            {/* Events */}
            <AnimatePresence>
              {timeline.events.map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="relative flex items-start gap-4"
                >
                  {/* Timeline Dot */}
                  <div className={`w-10 h-10 rounded-full bg-${getEventTypeColor(event.event_type)}-500 border-4 border-[#111827] flex items-center justify-center z-10 flex-shrink-0`}>
                    <span className="text-sm">{getEventIcon(event.event_type)}</span>
                  </div>
                  
                  {/* Event Content */}
                  <div className="flex-1 bg-black/50 p-4 rounded-lg border border-gray-700">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-white">{event.title}</h3>
                        <p className="text-sm text-gray-300 mt-1">{event.description}</p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {/* Completion Status */}
                        <button
                          onClick={() => handleUpdateEvent(event.id, { 
                            completed: !event.completed,
                            progress_percentage: event.completed ? 0 : 100
                          })}
                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                            event.completed 
                              ? 'bg-green-500 border-green-500' 
                              : 'bg-gray-600 border-gray-500 hover:border-green-500'
                          }`}
                        >
                          {event.completed && <span className="text-white text-xs">✓</span>}
                        </button>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="mb-2">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-gray-400">Progress</span>
                        <span className="text-xs text-gray-400">{event.progress_percentage.toFixed(0)}%</span>
                      </div>
                      <div className="bg-gray-700 rounded-full h-2 overflow-hidden">
                        <motion.div
                          className={`h-full ${getProgressColor(event.progress_percentage)}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${event.progress_percentage}%` }}
                          transition={{ duration: 0.5, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                    
                    {/* Event Metadata */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="capitalize">{getActivityTypeLabel(event.event_type)}</span>
                      <span>{formatTimestamp(event.timestamp)}</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  )
}
