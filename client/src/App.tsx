import { useState, useEffect } from "react"


function App() {
  const [message, setMessage] = useState<string>("")
  const API_URL = import.meta.env.VITE_API_URL

  useEffect(() => {
    const fetchMessage = async () => {
      const response = await fetch(`${API_URL}/`)
      const data = await response.json()
      setMessage(data.message)
    }
    fetchMessage()
  }, [])

  return (
    <>
      <h1 className="text-3xl font-bold">{message}</h1>
    </>
  )
}

export default App
