export type Mode = 'bus' | 'streetcar'

export interface VehicleRecord {
  vehicle_id: string
  mode: Mode
  route_id?: string
  route_short_name?: string
  trip_id?: string
  direction_id?: number
  headsign?: string
  lat: number
  lon: number
  bearing?: number
  timestamp?: string
  freshness_seconds?: number
  next_stop_id?: string
  next_stop_name?: string
  delay_seconds?: number
  alert_ids: string[]
}

export interface RouteRecord {
  route_id: string
  route_short_name?: string
  route_long_name?: string
  mode: Mode | 'other'
  shape_points: [number, number][]
}

export interface StopRecord {
  stop_id: string
  stop_name?: string
  lat: number
  lon: number
}

export interface AlertRecord {
  alert_id: string
  header?: string
  description?: string
  route_ids: string[]
  stop_ids: string[]
  effect?: string
  severity_level?: string
}
