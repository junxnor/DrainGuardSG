import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Health check
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Stations
  async getStations() {
    const response = await apiClient.get('/stations')
    return response.data
  },

  async getStation(stationId: string) {
    const response = await apiClient.get(`/stations/${stationId}`)
    return response.data
  },

  // Sensors
  async getSensors() {
    const response = await apiClient.get('/sensors')
    return response.data
  },

  // Rainfall
  async getLatestRainfall(limit: number = 100) {
    const response = await apiClient.get(`/rainfall/latest?limit=${limit}`)
    return response.data
  },

  async getRainfallHistory(params?: { start_date?: string; end_date?: string; station_id?: string }) {
    const response = await apiClient.get('/rainfall/history', { params })
    return response.data
  },

  async getStationRainfall(stationId: string, hours: number = 24) {
    const response = await apiClient.get(`/rainfall/station/${stationId}?hours=${hours}`)
    return response.data
  },

  // Risk Assessment
  async getRiskOverview() {
    const response = await apiClient.get('/risk/overview')
    return response.data
  },

  async getStationRisks() {
    const response = await apiClient.get('/risk/locations')
    return response.data
  },

  async getStationRisk(stationId: string) {
    const response = await apiClient.get(`/risk/station/${stationId}`)
    return response.data
  },

  // Recommendations
  async getRecommendations(riskLevel: string = 'moderate') {
    const response = await apiClient.get(`/recommendations?risk_level=${riskLevel}`)
    return response.data
  },

  async getAllRecommendations() {
    const response = await apiClient.get('/recommendations/all')
    return response.data
  },
}
