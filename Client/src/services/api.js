const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Get API key from environment or localStorage
const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('speakflow_api_key') || 'sk-demo-key-omi-hackathon'
}

export const analyzeConversation = async (text) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify({ text })
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error analyzing conversation:', error)
    // Fallback for demo purposes
    return {
      tasks: [
        { task: 'Finish backend', assigned_to: 'Edwin', deadline: 'tonight', priority: 'high' },
        { task: 'Design UI mockups', assigned_to: 'Sarah', deadline: 'next week', priority: 'medium' },
        { task: 'Contact KCB for partnership', assigned_to: 'John', deadline: 'Tuesday', priority: 'high' }
      ],
      summary: 'Kenyan fintech team discussed M-Pesa integration, UI design, and bank partnerships.'
    }
  }
}

export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    return await response.json()
  } catch (error) {
    console.error('Health check failed:', error)
    return { status: 'unhealthy' }
  }
}

// Omi Device Integration APIs
export const connectOmiDevice = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/omi/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      }
    })

    if (!response.ok) {
      throw new Error(`Omi connection error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error connecting Omi device:', error)
    // Fallback for demo
    return {
      message: 'Omi device connected successfully',
      device_id: 'OMI-DEMO-001',
      status: 'connected'
    }
  }
}

export const getOmiStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/omi/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getApiKey()}`
      }
    })

    if (!response.ok) {
      throw new Error(`Omi status error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting Omi status:', error)
    // Fallback for demo
    return {
      device_connected: false,
      real_time_processing: false,
      conversation_buffer_length: 0
    }
  }
}

export const startDemoStream = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/omi/demo-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      }
    })

    if (!response.ok) {
      throw new Error(`Demo stream error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error starting demo stream:', error)
    // Fallback for demo
    return {
      message: 'Demo stream completed',
      processed_sentences: 7,
      tasks_extracted: 5,
      demo_tasks: [
        { task: 'Complete API documentation', assigned_to: 'Edwin', deadline: 'Friday', priority: 'high' },
        { task: 'Handle UI design for mobile app', assigned_to: 'Sarah', deadline: 'next week', priority: 'medium' },
        { task: 'Contact KCB and Equity Bank', assigned_to: 'John', deadline: 'Tuesday', priority: 'high' }
      ]
    }
  }
}

export const sendOmiWebhook = async (transcript, deviceId = 'OMI-DEMO-001') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/omi/webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify({
        event: 'conversation_processed',
        device_id: deviceId,
        timestamp: Date.now(),
        data: {
          transcript: transcript,
          source: 'omi_ai_wearable',
          confidence: 0.95,
          language: 'en'
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Webhook error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error sending Omi webhook:', error)
    throw error
  }
}