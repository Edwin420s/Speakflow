import { useState, useEffect } from 'react'

export function useConversation(lines, intervalMs = 2000) {
  const [messages, setMessages] = useState([])

  useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      if (i < lines.length) {
        setMessages(prev => [...prev, lines[i]])
        i++
      } else {
        clearInterval(interval)
      }
    }, intervalMs)

    return () => clearInterval(interval)
  }, [lines, intervalMs])

  return messages
}