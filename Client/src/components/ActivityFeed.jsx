import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getActivityFeed, getActivityTypeLabel, getActivityTypeIcon, getActivityTypeColor } from '../services/activityService'

export default function ActivityFeed() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [filter, setFilter] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    fetchActivities()
    
    // Set up auto-refresh
    if (autoRefresh) {
      const interval = setInterval(fetchActivities, 10000) // Refresh every 10 seconds
      return () => clearInterval(interval)
    }
  }, [page, filter, autoRefresh])

  const fetchActivities = async () => {
    try {
      setLoading(true)
      const filters = filter ? { activity_type: filter } : {}
      const data = await getActivityFeed(page, 20, filters)
      
      if (page === 1) {
        setActivities(data.activities)
      } else {
        setActivities(prev => [...prev, ...data.activities])
      }
      
      setHasMore(data.has_more)
      setTotalCount(data.total_count)
    } catch (error) {
      console.error('Failed to fetch activities:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1)
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    
    return date.toLocaleDateString()
  }

  const getPriorityColor = (priority) => {
    const colors = {
      'urgent': 'bg-red-500',
      'high': 'bg-orange-500',
      'medium': 'bg-yellow-500',
      'low': 'bg-green-500'
    }
    return colors[priority] || 'bg-gray-500'
  }

  const getActivityColorClass = (type) => {
    const colorMap = {
      'task_created': 'bg-blue-500',
      'task_completed': 'bg-green-500',
      'task_assigned': 'bg-purple-500',
      'transcript_processed': 'bg-yellow-500',
      'trello_card_created': 'bg-orange-500',
      'whatsapp_sent': 'bg-teal-500',
      'omi_device_connected': 'bg-indigo-500',
      'omi_conversation_processed': 'bg-pink-500',
      'ai_processing_started': 'bg-gray-500',
      'ai_processing_completed': 'bg-emerald-500'
    }
    return colorMap[type] || 'bg-gray-500'
  }

  return (
    <div className="bg-[#111827] p-6 rounded-lg border border-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Activity Feed
          <span className="text-sm text-gray-400">({totalCount} activities)</span>
        </h2>
        
        <div className="flex items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 rounded text-sm transition ${
              autoRefresh 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            {autoRefresh ? '🔄 Auto' : '⏸️ Paused'}
          </button>
          
          {/* Filter dropdown */}
          <select
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value)
              setPage(1)
              setActivities([])
            }}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600"
          >
            <option value="">All Activities</option>
            <option value="task_created">Tasks</option>
            <option value="ai_processing_completed">AI Processing</option>
            <option value="trello_card_created">Trello</option>
            <option value="whatsapp_sent">WhatsApp</option>
            <option value="omi_conversation_processed">Omi Device</option>
          </select>
        </div>
      </div>

      {/* Activity List */}
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        <AnimatePresence>
          {activities.map((activity, index) => (
            <motion.div
              key={`${activity.id}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className="bg-black/50 p-4 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start gap-3">
                {/* Activity Icon */}
                <div className={`w-10 h-10 rounded-full ${getActivityColorClass(activity.type)}/20 flex items-center justify-center flex-shrink-0`}>
                  <span className="text-lg">{getActivityTypeIcon(activity.type)}</span>
                </div>
                
                {/* Activity Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium text-white truncate">
                      {activity.title}
                    </h3>
                    <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                      {formatTimestamp(activity.timestamp)}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-300 mb-2 line-clamp-2">
                    {activity.description}
                  </p>
                  
                  {/* Activity Metadata */}
                  {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                    <div className="flex flex-wrap gap-2 text-xs">
                      {Object.entries(activity.metadata).map(([key, value]) => {
                        if (key === 'priority' && value) {
                          return (
                            <span
                              key={key}
                              className={`px-2 py-1 rounded-full text-white ${getPriorityColor(value)}`}
                            >
                              {value}
                            </span>
                          )
                        }
                        
                        if (typeof value === 'number') {
                          return (
                            <span
                              key={key}
                              className="px-2 py-1 bg-gray-700 rounded-full text-gray-300"
                            >
                              {key.replace('_', ' ')}: {value}
                            </span>
                          )
                        }
                        
                        return null
                      })}
                    </div>
                  )}
                  
                  {/* Activity Type Badge */}
                  <div className="mt-2">
                    <span className="text-xs text-gray-500 capitalize">
                      {getActivityTypeLabel(activity.type)}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {loading && activities.length === 0 && (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
            Loading activities...
          </div>
        )}
        
        {!loading && activities.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📭</div>
            <p>No activities yet</p>
            <p className="text-sm">Start processing conversations to see activity</p>
          </div>
        )}
      </div>

      {/* Load More Button */}
      {hasMore && !loading && (
        <div className="mt-4 text-center">
          <button
            onClick={loadMore}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm transition"
          >
            Load More Activities
          </button>
        </div>
      )}
      
      {loading && activities.length > 0 && (
        <div className="mt-4 text-center text-gray-500 text-sm">
          Loading more activities...
        </div>
      )}
    </div>
  )
}
