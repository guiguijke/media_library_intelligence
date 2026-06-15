import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { SelectionProvider } from './contexts/SelectionContext'
import { ToastProvider } from './contexts/ToastContext'
import { ThemeProvider } from './contexts/ThemeContext'
import Navbar from './components/Navbar'
import TaskMonitor from './components/TaskMonitor'
import Dashboard from './pages/Dashboard'
import Discover from './pages/Discover'
import Queue from './pages/Queue'
import Wishlist from './pages/Wishlist'
import Settings from './pages/Settings'
import Activity from './pages/Activity'
import MediaDetail from './pages/MediaDetail'
import Login from './pages/Login'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('mli_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

function AppContent() {
  const location = useLocation()
  const isAuthenticated = !!localStorage.getItem('mli_token')
  const showTaskMonitor = isAuthenticated && location.pathname !== '/login'

  return (
    <div className="min-h-screen bg-background text-primary">
      <Navbar />
      <main className="pt-16">
        {showTaskMonitor && <TaskMonitor />}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/discover"
            element={
              <ProtectedRoute>
                <Discover />
              </ProtectedRoute>
            }
          />
          <Route
            path="/activity"
            element={
              <ProtectedRoute>
                <Activity />
              </ProtectedRoute>
            }
          />
          <Route
            path="/queue"
            element={
              <ProtectedRoute>
                <Queue />
              </ProtectedRoute>
            }
          />
          <Route
            path="/wishlist"
            element={
              <ProtectedRoute>
                <Wishlist />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/media/:id"
            element={
              <ProtectedRoute>
                <MediaDetail />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <SelectionProvider>
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </SelectionProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}

export default App
