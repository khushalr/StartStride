import { AlertRecord, RouteRecord, StopRecord, VehicleRecord } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function getVehicles(query = ''): Promise<{ updated_at_utc?: string; vehicles: VehicleRecord[] }> {
  return fetchJson(`/api/vehicles${query}`)
}

export function getRoutes(activeOnly = false): Promise<{ routes: RouteRecord[] }> {
  return fetchJson(`/api/routes${activeOnly ? '?active_only=true' : ''}`)
}

export function getStops(): Promise<{ stops: StopRecord[] }> {
  return fetchJson('/api/stops')
}

export function getAlerts(): Promise<{ alerts: AlertRecord[] }> {
  return fetchJson('/api/alerts')
}
