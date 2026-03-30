import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Suites from './pages/Suites'
import SuiteDetail from './pages/SuiteDetail'
import RunView from './pages/RunView'
import Prompts from './pages/Prompts'
import About from './pages/About'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/suites" element={<Suites />} />
        <Route path="/suite/:id" element={<SuiteDetail />} />
        <Route path="/run/:id" element={<RunView />} />
        <Route path="/prompts" element={<Prompts />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  )
}
