import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useAppStore } from '../store/appStore'

export default function RainfallChart() {
  const { stationRisks } = useAppStore()
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    if (stationRisks.length > 0) {
      // Sort by risk score and take top 10
      const topStations = [...stationRisks]
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, 10)
        .map((station) => ({
          name: station.station_name.split(' ').slice(0, 2).join(' '), // Shorten names
          '1hr': parseFloat(station.rainfall_1hr.toFixed(1)),
          '3hr': parseFloat(station.rainfall_3hr.toFixed(1)),
          score: parseFloat(station.risk_score.toFixed(1)),
        }))

      setChartData(topStations)
    }
  }, [stationRisks])

  if (chartData.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-slate-600">Loading rainfall data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full">
      <div className="text-sm text-slate-600 mb-4">
        <p>Top 10 stations by accumulated rainfall</p>
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 10, left: -20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 10 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            label={{ value: 'Rainfall (mm)', angle: -90, position: 'insideLeft', fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '0.5rem',
              fontSize: '12px',
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="square"
          />
          <Bar dataKey="1hr" fill="#3b82f6" name="1 Hour" radius={[4, 4, 0, 0]} />
          <Bar dataKey="3hr" fill="#60a5fa" name="3 Hours" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
