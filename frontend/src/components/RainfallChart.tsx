import { useEffect, useMemo, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useAppStore } from '../store/appStore'
import { freshStationRisks } from '../utils/freshness'

export default function RainfallChart() {
  const { stationRisks: rawRisks, now } = useAppStore()
  const stationRisks = useMemo(() => freshStationRisks(rawRisks, now), [rawRisks, now])
  const [chartData, setChartData] = useState<any[]>([])

  const reporting = useMemo(() => stationRisks.filter((s) => s.data_status === 'ok'), [stationRisks])

  useEffect(() => {
    if (reporting.length > 0) {
      // Stations with current official data, sorted by risk score, top 10
      const topStations = [...reporting]
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, 10)
        .map((station) => ({
          name: station.station_name.split(' ').slice(0, 2).join(' '), // Shorten names
          '1hr': parseFloat(station.rainfall_1hr.toFixed(1)),
          '3hr': parseFloat(station.rainfall_3hr.toFixed(1)),
          score: parseFloat(station.risk_score.toFixed(1)),
        }))

      setChartData(topStations)
    } else {
      setChartData([])
    }
  }, [reporting])

  // Risk data has loaded but no station has current official readings
  if (stationRisks.length > 0 && reporting.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-sm text-slate-600 px-4">
          <p className="font-medium text-slate-800">No current rainfall data</p>
          <p className="mt-1">{stationRisks[0].data_note || 'Official readings are unavailable right now.'}</p>
        </div>
      </div>
    )
  }

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
        <p>Top stations by risk score · official data.gov.sg readings</p>
        {chartData.every((d) => d['3hr'] === 0) && (
          <p className="text-xs mt-1">No rain recorded at these stations in the last 3 hours.</p>
        )}
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
