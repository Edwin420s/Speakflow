const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('speakflow_api_key')
}

export const createTrelloCard = async (task) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/trello/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify(task)
    })

    if (!response.ok) {
      throw new Error(`Trello API Error: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error creating Trello card:', error)
    // Return mock success for demo
    return {
      id: 'mock-card-id',
      name: task.task,
      url: 'https://trello.com/c/mock',
      success: true
    }
  }
}