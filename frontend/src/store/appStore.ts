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

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical' | 'no_data'

export interface StationRisk {
  station_id: string
  station_name: string
  longitude: number
  latitude: number
  risk_level: RiskLevel
  risk_score: number
  current_rainfall: number
  rainfall_15min: number
  rainfall_1hr: number
  rainfall_3hr: number
  readings_3hr: number
  data_status: 'ok' | 'no_data'
  data_note: string | null
  source: string
  observed_at: string | null
  last_updated: string | null
}

export interface RiskOverview {
  overall_risk: RiskLevel
  risk_score: number
  high_risk_count: number
  moderate_risk_count: number
  low_risk_count: number
  critical_count: number
  no_data_count: number
  total_stations: number
  stations_with_data: number
  data_status: 'ok' | 'no_data'
  data_note: string | null
  source: string
  last_updated: string | null
  high_risk_stations: string[]
  ingestion_state: string
  ingestion_last_success_at: string | null
}

interface AppState {
  stations: Station[]
  sensors: Sensor[]
  stationRisks: StationRisk[]
  riskOverview: RiskOverview | null
  selectedStation: string | null
  loading: boolean
  error: string | null
  now: number // updated every minute so freshness checks re-run

  fetchStations: () => Promise<void>
  fetchSensors: () => Promise<void>
  fetchRiskOverview: () => Promise<void>
  fetchStationRisks: () => Promise<void>
  refreshRisk: () => Promise<void>
  tick: () => void
  setSelectedStation: (stationId: string | null) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  stations: [],
  sensors: [],
  stationRisks: [],
  riskOverview: null,
  selectedStation: null,
  loading: false,
  error: null,
  now: Date.now(),

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

  // Overview cards, map colours and chart all come from these two responses
  refreshRisk: async () => {
    await Promise.all([get().fetchRiskOverview(), get().fetchStationRisks()])
    set({ now: Date.now() })
  },

  tick: () => set({ now: Date.now() }),

  setSelectedStation: (stationId) => {
    set({ selectedStation: stationId })
  },
}))
