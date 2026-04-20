import { useEffect, useMemo, useState } from 'react'
import { FiltersPanel } from './components/FiltersPanel'
import { LiveMap } from './components/LiveMap'
import { getAlerts, getRoutes, getStops, getVehicles } from './lib/api'
import { AlertRecord, RouteRecord, StopRecord, VehicleRecord } from './lib/types'

const POLL_MS = 15_000

function buildVehicleQuery(routeFilter: string, modeFilter: string, directionFilter: string): string {
  const params = new URLSearchParams()
  if (routeFilter) params.append('route_id', routeFilter)
  if (modeFilter) params.append('mode', modeFilter)
  if (directionFilter) params.append('direction_id', directionFilter)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export default function App() {
  const [vehicles, setVehicles] = useState<VehicleRecord[]>([])
  const [routes, setRoutes] = useState<RouteRecord[]>([])
  const [stops, setStops] = useState<StopRecord[]>([])
  const [alerts, setAlerts] = useState<AlertRecord[]>([])

  const [routeFilter, setRouteFilter] = useState('')
  const [modeFilter, setModeFilter] = useState<'' | 'bus' | 'streetcar'>('')
  const [directionFilter, setDirectionFilter] = useState<'' | '0' | '1'>('')

  const [updatedAt, setUpdatedAt] = useState<string | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const query = useMemo(
    () => buildVehicleQuery(routeFilter, modeFilter, directionFilter),
    [routeFilter, modeFilter, directionFilter]
  )

  useEffect(() => {
    let cancelled = false

    async function loadData() {
      try {
        setError(null)
        const [vehiclesResp, routesResp, stopsResp, alertsResp] = await Promise.all([
          getVehicles(query),
          getRoutes(),
          getStops(),
          getAlerts()
        ])

        if (cancelled) return

        setVehicles(vehiclesResp.vehicles)
        setUpdatedAt(vehiclesResp.updated_at_utc)
        setRoutes(routesResp.routes)
        setStops(stopsResp.stops)
        setAlerts(alertsResp.alerts)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown API error')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadData()
    const timer = setInterval(loadData, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [query])

  return (
    <div className="layout">
      <header>
        <h1>TTC Live Transit Map (MVP)</h1>
        <p>Surface network only (bus + streetcar). Refreshes every {POLL_MS / 1000}s.</p>
      </header>

      <FiltersPanel
        routes={routes}
        routeFilter={routeFilter}
        modeFilter={modeFilter}
        directionFilter={directionFilter}
        onRouteFilter={setRouteFilter}
        onModeFilter={setModeFilter}
        onDirectionFilter={setDirectionFilter}
      />

      <main>
        {loading && <div className="status">Loading transit feeds…</div>}
        {error && <div className="status error">{error}</div>}
        {!loading && !error && vehicles.length === 0 && <div className="status">No active vehicles for current filters.</div>}

        <LiveMap vehicles={vehicles} routes={routes} stops={stops} />

        <section className="meta">
          <h2>Service alerts ({alerts.length})</h2>
          <ul>
            {alerts.map((alert) => (
              <li key={alert.alert_id}>
                <strong>{alert.header ?? alert.alert_id}</strong>
                <span>{alert.description ?? 'No additional details.'}</span>
              </li>
            ))}
          </ul>

          <p className="updated">Last feed refresh: {updatedAt ?? 'N/A'}</p>
        </section>
      </main>
    </div>
  )
}
