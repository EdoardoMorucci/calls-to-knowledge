import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CallsList } from './pages/CallsList'
import { CallDetail } from './pages/CallDetail'
import { ProjectDashboard } from './pages/ProjectDashboard'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10_000 } },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/calls" replace />} />
          <Route path="/calls" element={<CallsList />} />
          <Route path="/calls/:id" element={<CallDetail />} />
          <Route path="/projects/:id" element={<ProjectDashboard />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
