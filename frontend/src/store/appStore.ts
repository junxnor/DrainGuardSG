import { create } from 'zustand'
import { api } from '../services/api'

export interface Station {
  station_id: string
  station_name: string
  device_id?: string
  longitude: number
  latitude: number
}

export interface Sensor {
  station_id: string
  station_name: string
  longitude: number
  latitude: number
}

export interface StationRisk {
  station_id: string
  station_name: string
  longitude: number
  latitude: number
  risk_level: 'low' | 'moderate' | 'high' | 'critical'
  risk_score: number
  current_rainfall: number
  rainfall_1hr: number
  rainfall_3hr: number
  last_updated: string
}

export interface RiskOverview {
  overall_risk: string
  risk_score: number
  high_risk_count: number
  moderate_risk_count: number
  low_risk_count: number
  total_stations: number
  last_updated: string
  high_risk_stations: string[]
}

interface AppState {
  stations: Station[]
  sensors: Sensor[]
  stationRisks: StationRisk[]
  riskOverview: RiskOverview | null
  selectedStation: string | null
  loading: boolean
  error: string | null

  fetchStations: () => Promise<void>
  fetchSensors: () => Promise<void>
  fetchRiskOverview: () => Promise<void>
  fetchStationRisks: () => Promise<void>
  setSelectedStation: (stationId: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  stations: [],
  sensors: [],
  stationRisks: [],
  riskOverview: null,
  selectedStation: null,
  loading: false,
  error: null,

  fetchStations: async () => {
    try {
      set({ loading: true, error: null })
      const stations = await api.getStations()
      set({ stations, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchSensors: async () => {
    try {
      const sensors = await api.getSensors()
      set({ sensors })
    } catch (error: any) {
      console.error('Failed to fetch sensors:', error)
    }
  },

  fetchRiskOverview: async () => {
    try {
      const riskOverview = await api.getRiskOverview()
      set({ riskOverview })
    } catch (error: any) {
      console.error('Failed to fetch risk overview:', error)
    }
  },

  fetchStationRisks: async () => {
    try {
      const stationRisks = await api.getStationRisks()
      set({ stationRisks })
    } catch (error: any) {
      console.error('Failed to fetch station risks:', error)
    }
  },

  setSelectedStation: (stationId) => {
    set({ selectedStation: stationId })
  },
}))
