import { useEffect, useMemo } from 'react'
import { AlertTriangle, Cloud, Droplets, TrendingUp } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { freshOverview } from '../utils/freshness'

export default function RiskOverview() {
  const { riskOverview: rawOverview, fetchRiskOverview, now } = useAppStore()
  const riskOverview = useMemo(() => freshOverview(rawOverview, now), [rawOverview, now])

  useEffect(() => {
    fetchRiskOverview()
  }, [fetchRiskOverview])

  if (!riskOverview) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-slate-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  const noData = riskOverview.data_status === 'no_data'

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'no_data':
        return 'bg-slate-100 text-slate-700 border-slate-300'
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low':
      default:
        return 'bg-green-100 text-green-800 border-green-300'
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Overall Risk */}
      <div className={`rounded-lg shadow-md p-6 border-2 ${getRiskColor(riskOverview.overall_risk)}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="text-sm font-medium">Overall Risk</h3>
          </div>
        </div>
        <p className="text-3xl font-bold capitalize">{noData ? 'No data' : riskOverview.overall_risk}</p>
        <p className="text-xs mt-1 opacity-75">
          {noData
            ? riskOverview.data_note || 'Official rainfall data unavailable'
            : `Score: ${riskOverview.risk_score.toFixed(1)}/100 · ${riskOverview.stations_with_data}/${riskOverview.total_stations} stations reporting`}
        </p>
      </div>

      {/* High Risk Areas */}
      <div className="bg-white rounded-lg shadow-md p-6 border-2 border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Cloud className="w-5 h-5 text-orange-600" />
            <h3 className="text-sm font-medium text-slate-700">High Risk Areas</h3>
          </div>
        </div>
        <p className="text-3xl font-bold text-slate-900">{riskOverview.high_risk_count}</p>
        <p className="text-xs text-slate-600 mt-1">Stations requiring attention</p>
      </div>

      {/* Moderate Risk */}
      <div className="bg-white rounded-lg shadow-md p-6 border-2 border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-yellow-600" />
            <h3 className="text-sm font-medium text-slate-700">Moderate Risk</h3>
          </div>
        </div>
        <p className="text-3xl font-bold text-slate-900">{riskOverview.moderate_risk_count}</p>
        <p className="text-xs text-slate-600 mt-1">Stations under monitoring</p>
      </div>

      {/* Total Stations */}
      <div className="bg-white rounded-lg shadow-md p-6 border-2 border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Droplets className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-medium text-slate-700">Active Stations</h3>
          </div>
        </div>
        <p className="text-3xl font-bold text-slate-900">{riskOverview.total_stations}</p>
        <p className="text-xs text-slate-600 mt-1">Monitoring across Singapore</p>
      </div>
    </div>
  )
}
