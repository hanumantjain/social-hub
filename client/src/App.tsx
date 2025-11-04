import { Route, Routes, useNavigate } from "react-router-dom"
import { useEffect } from "react"
import Login from "./pages/Login"
import Signup from "./pages/Signup"
import Feed from "./pages/Feed"
import Profile from "./pages/Profile"
import Upload from "./pages/Upload"
import PostDetail from "./pages/PostDetail"
import { setAuthErrorHandler } from "./services/api"

function App() {
  const navigate = useNavigate()

  useEffect(() => {
    // Set up global auth error handler
    setAuthErrorHandler(() => {
      // Redirect to login with current path as redirect parameter
      const currentPath = window.location.pathname
      navigate(`/login?redirect=${encodeURIComponent(currentPath)}`)
    })
  }, [navigate])
  
  return (
    <div className="min-h-screen bg-white">
      <div className="bg-[linear-gradient(rgba(0,0,0,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,.05)_1px,transparent_1px)] bg-[size:100px_100px] min-h-screen">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/post/:id" element={<PostDetail />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
