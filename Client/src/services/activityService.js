const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('speakflow_api_key') || 'sk-demo-key-omi-hackathon'
}

// Activity Feed API
export const getActivityFeed = async (page = 1, pageSize = 20, filters = {}) => {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters
    })

    const response = await fetch(`${API_BASE_URL}/api/activities?${params}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getApiKey()}`
      }
    })

    if (!response.ok) {
      throw new Error(`Activity feed error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching activity feed:', error)
    // Return mock data for demo
    return {
      activities: [
        {
          id: 1,
          type: 'ai_processing_started',
          title: 'AI Processing Started',
          description: 'Processing transcript of 1250 characters',
          timestamp: new Date().toISOString(),
          metadata: { text_length: 1250, client_ip: '127.0.0.1' }
        },
        {
          id: 2,
          type: 'transcript_processed',
          title: 'Transcript Processed',
          description: 'Successfully processed transcript and extracted 5 tasks',
          timestamp: new Date(Date.now() - 60000).toISOString(),
          metadata: { tasks_count: 5, summary_length: 180, processing_time_ms: 2340 }
        },
        {
          id: 3,
          type: 'trello_card_created',
          title: 'Trello Cards Created',
          description: 'Created 5 Trello cards',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          metadata: { card_count: 5, cards: ['card1', 'card2', 'card3', 'card4', 'card5'] }
        }
      ],
      total_count: 3,
      page: 1,
      page_size: 20,
      has_more: false
    }
  }
}

// Timeline API
export const getTimeline = async (filters = {}) => {
  try {
    const params = new URLSearchParams(filters)

    const response = await fetch(`${API_BASE_URL}/api/timeline?${params}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getApiKey()}`
      }
    })

    if (!response.ok) {
      throw new Error(`Timeline error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching timeline:', error)
    // Return mock data for demo
    return {
      events: [
        {
          id: 1,
          title: 'Meeting Started',
          description: 'Team meeting for fintech app discussion',
          event_type: 'transcript_processed',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          completed: true,
          progress_percentage: 100,
          metadata: { meeting_type: 'planning' }
        },
        {
          id: 2,
          title: 'Task Extraction',
          description: 'AI extracted 5 action items from conversation',
          event_type: 'ai_processing_completed',
          timestamp: new Date(Date.now() - 3000000).toISOString(),
          completed: true,
          progress_percentage: 100,
          metadata: { tasks_extracted: 5, confidence: 0.85 }
        },
        {
          id: 3,
          title: 'Trello Integration',
          description: 'Creating cards in project management board',
          event_type: 'trello_card_created',
          timestamp: new Date(Date.now() - 2400000).toISOString(),
          completed: true,
          progress_percentage: 100,
          metadata: { cards_created: 5 }
        },
        {
          id: 4,
          title: 'WhatsApp Summary',
          description: 'Sending meeting summary to team',
          event_type: 'whatsapp_sent',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          completed: true,
          progress_percentage: 100,
          metadata: { recipients: 3, message_length: 450 }
        },
        {
          id: 5,
          title: 'Follow-up Tasks',
          description: 'Pending follow-up actions for next meeting',
          event_type: 'task_created',
          timestamp: new Date(Date.now() - 1200000).toISOString(),
          completed: false,
          progress_percentage: 25,
          metadata: { pending_tasks: 2, next_deadline: '2024-01-15' }
        }
      ],
      total_events: 5,
      completion_percentage: 80,
      start_date: new Date(Date.now() - 3600000).toISOString(),
      end_date: new Date(Date.now() - 1200000).toISOString(),
      active_tasks: 2,
      completed_tasks: 3
    }
  }
}

// Create Timeline Event
export const createTimelineEvent = async (eventData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/timeline/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify(eventData)
    })

    if (!response.ok) {
      throw new Error(`Create timeline event error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error creating timeline event:', error)
    // Return mock success for demo
    return {
      id: Date.now(),
      title: eventData.title,
      description: eventData.description,
      event_type: eventData.event_type,
      timestamp: new Date().toISOString(),
      completed: false,
      progress_percentage: 0,
      related_task_id: eventData.related_task_id || null,
      metadata: eventData.metadata || {}
    }
  }
}

// Update Timeline Event
export const updateTimelineEvent = async (eventId, eventData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/timeline/events/${eventId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify(eventData)
    })

    if (!response.ok) {
      throw new Error(`Update timeline event error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error updating timeline event:', error)
    // Return mock success for demo
    return {
      id: eventId,
      title: eventData.title || 'Updated Event',
      description: eventData.description || 'Updated description',
      event_type: 'task_created',
      timestamp: new Date().toISOString(),
      completed: eventData.completed || false,
      progress_percentage: eventData.progress_percentage || 0,
      related_task_id: eventData.related_task_id || null,
      metadata: eventData.metadata || {}
    }
  }
}

// Activity type utilities
export const getActivityTypeLabel = (type) => {
  const labels = {
    'task_created': 'Task Created',
    'task_completed': 'Task Completed',
    'task_assigned': 'Task Assigned',
    'transcript_processed': 'Transcript Processed',
    'trello_card_created': 'Trello Card Created',
    'whatsapp_sent': 'WhatsApp Sent',
    'omi_device_connected': 'Omi Device Connected',
    'omi_conversation_processed': 'Omi Conversation Processed',
    'ai_processing_started': 'AI Processing Started',
    'ai_processing_completed': 'AI Processing Completed'
  }
  return labels[type] || type
}

export const getActivityTypeIcon = (type) => {
  const icons = {
    'task_created': '📋',
    'task_completed': '✅',
    'task_assigned': '👤',
    'transcript_processed': '📝',
    'trello_card_created': '📌',
    'whatsapp_sent': '💬',
    'omi_device_connected': '🎤',
    'omi_conversation_processed': '🎧',
    'ai_processing_started': '🤖',
    'ai_processing_completed': '🧠'
  }
  return icons[type] || '📄'
}

export const getActivityTypeColor = (type) => {
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
  return colors[type] || 'gray'
}
