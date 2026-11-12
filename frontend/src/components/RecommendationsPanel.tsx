import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, CheckCircle, Info, AlertTriangle, Eye, Package, Droplet, Wrench, Map, Cloud, Activity } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { api } from '../services/api'
import { freshOverview } from '../utils/freshness'

interface Recommendation {
  category: string
  priority: string
  title: string
  description: string
  icon: string
}

const getIcon = (iconName: string) => {
  const icons: { [key: string]: any } = {
    'alert-circle': AlertCircle,
    'alert-triangle': AlertTriangle,
    'check-circle': CheckCircle,
    'info': Info,
    'eye': Eye,
    'package': Package,
    'droplet': Droplet,
    'tool': Wrench,
    'map': Map,
    'cloud': Cloud,
    'car': Activity,
  }
  return icons[iconName] || Info
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-50 border-red-200 text-red-900'
    case 'high':
      return 'bg-orange-50 border-orange-200 text-orange-900'
    case 'medium':
      return 'bg-yellow-50 border-yellow-200 text-yellow-900'
    case 'low':
    default:
      return 'bg-blue-50 border-blue-200 text-blue-900'
  }
}

const getPriorityBadge = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-100 text-red-800'
    case 'high':
      return 'bg-orange-100 text-orange-800'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800'
    case 'low':
    default:
      return 'bg-blue-100 text-blue-800'
  }
}

export default function RecommendationsPanel() {
  const { riskOverview: rawOverview, now } = useAppStore()
  const riskOverview = useMemo(() => freshOverview(rawOverview, now), [rawOverview, now])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)

  const level = riskOverview?.overall_risk

  // Reload only when the risk level changes, not on every 5-minute refresh
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (level) {
        try {
          setLoading(true)
          const recs = await api.getRecommendations(level)
          setRecommendations(recs)
        } catch (error) {
          console.error('Failed to fetch recommendations:', error)
        } finally {
          setLoading(false)
        }
      }
    }

    fetchRecommendations()
  }, [level])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Preventive Recommendations
        </h3>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Preventive Recommendations
        </h3>
        {riskOverview && (
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityBadge(riskOverview.overall_risk)}`}>
            {riskOverview.overall_risk === 'no_data'
              ? 'General advice · rainfall data unavailable'
              : `Based on ${riskOverview.overall_risk} risk level`}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((rec, index) => {
          const IconComponent = getIcon(rec.icon)
          return (
            <div
              key={index}
              className={`border-2 rounded-lg p-4 ${getPriorityColor(rec.priority)}`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  <IconComponent className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold">{rec.title}</h4>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadge(rec.priority)}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="text-sm opacity-90">{rec.description}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Official Resources */}
      <div className="mt-6 pt-6 border-t border-slate-200">
        <h4 className="text-sm font-semibold text-slate-900 mb-3">Official Resources</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <a
            href="https://www.pub.gov.sg"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
          >
            <Activity className="w-4 h-4" />
            <span>PUB Flash Flood Alerts</span>
          </a>
          <a
            href="https://www.weather.gov.sg"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
          >
            <Cloud className="w-4 h-4" />
            <span>NEA Weather Forecast</span>
          </a>
        </div>
      </div>
    </div>
  )
}
