import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import { useAppStore } from '../store/appStore'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icons in React-Leaflet
// @ts-ignore
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
// @ts-ignore
import markerIcon from 'leaflet/dist/images/marker-icon.png'
// @ts-ignore
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

// Risk level colors
const getRiskColor = (riskLevel: string) => {
  switch (riskLevel) {
    case 'critical':
      return '#ef4444'
    case 'high':
      return '#f97316'
    case 'moderate':
      return '#f59e0b'
    case 'low':
    default:
      return '#10b981'
  }
}

// Create custom markers for stations
const createStationIcon = (riskLevel: string) => {
  const color = getRiskColor(riskLevel)
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background-color: ${color};
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

// Map Legend Component
function MapLegend() {
  return (
    <div className="absolute bottom-6 left-6 bg-white rounded-lg shadow-lg p-4 z-[1000]">
      <h4 className="font-semibold text-sm mb-2">Risk Levels</h4>
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-risk-low border-2 border-white"></div>
          <span className="text-xs">Low (0-25)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-risk-moderate border-2 border-white"></div>
          <span className="text-xs">Moderate (26-50)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-risk-high border-2 border-white"></div>
          <span className="text-xs">High (51-75)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-risk-critical border-2 border-white"></div>
          <span className="text-xs">Critical (76-100)</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-200">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-blue-500 opacity-30"></div>
          <span className="text-xs">PUB Sensors</span>
        </div>
      </div>
    </div>
  )
}

export default function MapComponent() {
  const { stations, sensors, stationRisks, fetchStationRisks } = useAppStore()
  const [mapLoaded, setMapLoaded] = useState(false)

  // Singapore center coordinates
  const singaporeCenter: [number, number] = [1.3521, 103.8198]

  useEffect(() => {
    // Fetch risk data when component mounts
    if (stations.length > 0) {
      fetchStationRisks()
    }
  }, [stations, fetchStationRisks])

  // Get risk level for a station
  const getStationRisk = (stationId: string) => {
    const risk = stationRisks.find((r) => r.station_id === stationId)
    return risk?.risk_level || 'low'
  }

  const getStationRiskData = (stationId: string) => {
    return stationRisks.find((r) => r.station_id === stationId)
  }

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={singaporeCenter}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full"
        whenReady={() => setMapLoaded(true)}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Rainfall Stations */}
        {stations.map((station) => {
          const riskLevel = getStationRisk(station.station_id)
          const riskData = getStationRiskData(station.station_id)
          
          return (
            <Marker
              key={station.station_id}
              position={[station.latitude, station.longitude]}
              icon={createStationIcon(riskLevel)}
            >
              <Popup>
                <div className="min-w-[200px]">
                  <h3 className="font-semibold text-base mb-2">{station.station_name}</h3>
                  <div className="text-sm space-y-1">
                    <p><span className="font-medium">Station ID:</span> {station.station_id}</p>
                    {riskData && (
                      <>
                        <p><span className="font-medium">Risk Level:</span> 
                          <span className={`ml-1 px-2 py-0.5 rounded text-xs font-medium risk-${riskLevel}`}>
                            {riskLevel.toUpperCase()}
                          </span>
                        </p>
                        <p><span className="font-medium">Risk Score:</span> {riskData.risk_score}</p>
                        <p><span className="font-medium">Current Rainfall:</span> {riskData.current_rainfall} mm</p>
                        <p><span className="font-medium">1hr Total:</span> {riskData.rainfall_1hr} mm</p>
                        <p><span className="font-medium">3hr Total:</span> {riskData.rainfall_3hr} mm</p>
                      </>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* PUB Sensors (smaller markers) */}
        {sensors.map((sensor) => (
          <CircleMarker
            key={sensor.station_id}
            center={[sensor.latitude, sensor.longitude]}
            radius={5}
            pathOptions={{
              fillColor: '#3b82f6',
              fillOpacity: 0.3,
              color: '#2563eb',
              weight: 1,
            }}
          >
            <Popup>
              <div className="min-w-[180px]">
                <h3 className="font-semibold text-sm mb-1">PUB Water Sensor</h3>
                <p className="text-sm">{sensor.station_name}</p>
                <p className="text-xs text-slate-600 mt-1">ID: {sensor.station_id}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Map Legend */}
      <MapLegend />

      {/* Loading Indicator */}
      {!mapLoaded && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-[1000]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-slate-600">Loading map...</p>
          </div>
        </div>
      )}
    </div>
  )
}
