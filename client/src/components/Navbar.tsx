import { Link, useNavigate } from "react-router-dom"
import { tokenManager } from "../services/api"
import { useState, useEffect } from "react"

const Navbar = () => {
  const navigate = useNavigate()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check authentication status on component mount and on route changes
    const checkAuth = () => {
      setIsAuthenticated(tokenManager.isAuthenticated())
    }
    
    checkAuth()
    
    // Check auth status when the component re-renders (e.g., after login/signup)
    const interval = setInterval(checkAuth, 1000)
    
    return () => clearInterval(interval)
  }, [])

  const handleLogout = () => {
    tokenManager.removeToken()
    setIsAuthenticated(false)
    navigate("/")
  }

  return (
    <nav className="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-12 sm:h-16">
          {/* Left side - Name/Brand */}
          <div className="flex-shrink-0">
            <Link to="/" className="text-lg sm:text-xl font-bold text-gray-900 hover:text-gray-700 transition-colors">
            GalleryAI
            </Link>
          </div>
          
          {/* Right side - Navigation buttons */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Upload button - Always visible */}
            <Link
              to="/upload"
              className="text-gray-700 hover:text-gray-900 px-2 sm:px-3 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors flex items-center"
            >
              <svg className="w-4 h-4 sm:w-5 sm:h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="hidden sm:inline">Upload</span>
            </Link>

            {isAuthenticated ? (
              <>
                {/* Logged in - Show Profile and Logout */}
                <Link
                  to="/profile"
                  className="text-gray-700 hover:text-gray-900 px-2 sm:px-3 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors"
                >
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                {/* Not logged in - Show Login and Signup */}
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-gray-900 px-2 sm:px-3 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="bg-black hover:bg-gray-800 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
