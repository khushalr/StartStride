import { RouteRecord } from '../lib/types'

interface Props {
  routes: RouteRecord[]
  routeFilter: string
  modeFilter: '' | 'bus' | 'streetcar'
  directionFilter: '' | '0' | '1'
  onRouteFilter: (route: string) => void
  onModeFilter: (mode: '' | 'bus' | 'streetcar') => void
  onDirectionFilter: (direction: '' | '0' | '1') => void
}

export function FiltersPanel(props: Props) {
  const filteredRoutes = props.routes.filter((r) => r.mode === 'bus' || r.mode === 'streetcar')

  return (
    <aside className="panel">
      <h2>Filters</h2>

      <label>
        Route
        <select value={props.routeFilter} onChange={(e) => props.onRouteFilter(e.target.value)}>
          <option value="">All routes</option>
          {filteredRoutes.map((route) => (
            <option key={route.route_id} value={route.route_id}>
              {route.route_short_name ?? route.route_id} — {route.route_long_name ?? 'Unnamed'}
            </option>
          ))}
        </select>
      </label>

      <label>
        Mode
        <select value={props.modeFilter} onChange={(e) => props.onModeFilter(e.target.value as '' | 'bus' | 'streetcar')}>
          <option value="">Bus + Streetcar</option>
          <option value="bus">Bus only</option>
          <option value="streetcar">Streetcar only</option>
        </select>
      </label>

      <label>
        Direction
        <select
          value={props.directionFilter}
          onChange={(e) => props.onDirectionFilter(e.target.value as '' | '0' | '1')}
        >
          <option value="">Both directions</option>
          <option value="0">Direction 0</option>
          <option value="1">Direction 1</option>
        </select>
      </label>

      <div className="legend">
        <h3>Legend</h3>
        <p><span className="dot bus" /> Bus</p>
        <p><span className="dot streetcar" /> Streetcar</p>
        <p><span className="line route" /> Route shape</p>
        <p><span className="dot stop" /> Stop marker (zoomed in)</p>
      </div>
    </aside>
  )
}
