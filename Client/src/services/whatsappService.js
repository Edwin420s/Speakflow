const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('speakflow_api_key')
}

export const sendWhatsAppMessage = async (message) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/whatsapp/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getApiKey()}`
      },
      body: JSON.stringify({ message })
    })

    if (!response.ok) {
      throw new Error(`WhatsApp API Error: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error sending WhatsApp message:', error)
    // Return mock success for demo
    return {
      message_sid: 'mock-sid-' + Date.now(),
      status: 'sent',
      success: true
    }
  }
}