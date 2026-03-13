const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Get API key from environment or localStorage
const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('speakflow_api_key')
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
        { task: 'Finish backend', assigned_to: 'Edwin', deadline: 'tonight' }
      ],
      summary: 'Team discussed backend progress.'
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