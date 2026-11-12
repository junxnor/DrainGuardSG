import { useEffect } from 'react'
import { Cloud, AlertTriangle, Droplets, Activity } from 'lucide-react'
import MapComponent from './components/MapComponent.tsx'
import RiskOverview from './components/RiskOverview.tsx'
import RainfallChart from './components/RainfallChart.tsx'
import RecommendationsPanel from './components/RecommendationsPanel.tsx'
import { useAppStore } from './store/appStore.ts'
import './App.css'

function App() {
  const { fetchStations, fetchSensors, fetchRiskOverview, loading, error } = useAppStore()

  useEffect(() => {
    // Initial data fetch
    const loadData = async () => {
      await Promise.all([
        fetchStations(),
        fetchSensors(),
        fetchRiskOverview()
      ])
    }
    loadData()

    // Refresh risk data every 5 minutes
    const interval = setInterval(() => {
      fetchRiskOverview()
    }, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [fetchStations, fetchSensors, fetchRiskOverview])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Droplets className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">DrainGuard Singapore</h1>
                <p className="text-sm text-slate-600">AI-Powered Rainfall Risk Monitoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <Activity className="w-4 h-4" />
                <span>Live Monitoring</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {/* Risk Overview Cards */}
        <div className="mb-6">
          <RiskOverview />
        </div>

        {/* Map and Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Map - Takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '600px' }}>
              <MapComponent />
            </div>
          </div>

          {/* Rainfall Chart */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6" style={{ height: '600px' }}>
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <Cloud className="w-5 h-5 mr-2 text-blue-600" />
                Rainfall Intensity
              </h3>
              <RainfallChart />
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <RecommendationsPanel />

        {/* Footer Disclaimer */}
        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold mb-1">Important Disclaimer</p>
              <p>
                This system provides rainfall-based risk estimation, NOT flood prediction. 
                Risk scores are calculated based on rainfall intensity thresholds and do not represent 
                actual flood forecasts. Always refer to official PUB (Public Utilities Board) flood 
                alerts for authoritative information.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-slate-600">
            <p>Data Source: data.gov.sg • PUB Singapore</p>
            <p className="mt-1">DrainGuard Singapore © 2026 • Built for Urban Flood Prevention</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
