import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { SelectionProvider } from './contexts/SelectionContext'
import Navbar from './components/Navbar'
import TaskMonitor from './components/TaskMonitor'
import Dashboard from './pages/Dashboard'
import Discover from './pages/Discover'
import Queue from './pages/Queue'
import Wishlist from './pages/Wishlist'
import Settings from './pages/Settings'
import Activity from './pages/Activity'

function App() {
  return (
    <SelectionProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-background text-primary">
          <Navbar />
          <main className="pt-16">
            <TaskMonitor />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/discover" element={<Discover />} />
              <Route path="/activity" element={<Activity />} />
              <Route path="/queue" element={<Queue />} />
              <Route path="/wishlist" element={<Wishlist />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </SelectionProvider>
  )
}

export default App
