import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import MarkerClusterGroup from 'react-leaflet-markercluster'
import { CircleMarker, MapContainer, Marker, Popup, Polyline, TileLayer, useMapEvents } from 'react-leaflet'
import { RouteRecord, StopRecord, VehicleRecord } from '../lib/types'

interface Props {
  vehicles: VehicleRecord[]
  routes: RouteRecord[]
  stops: StopRecord[]
}

const busIcon = L.divIcon({ className: 'vehicle-icon bus', html: '🚌', iconSize: [22, 22] })
const streetcarIcon = L.divIcon({ className: 'vehicle-icon streetcar', html: '🚋', iconSize: [22, 22] })

function ZoomAwareStops({ stops }: { stops: StopRecord[] }) {
  const map = useMapEvents({})
  const showStops = map.getZoom() >= 13

  if (!showStops) return null

  return (
    <>
      {stops.map((stop) => (
        <CircleMarker key={stop.stop_id} center={[stop.lat, stop.lon]} radius={3} pathOptions={{ color: '#525252' }}>
          <Popup>
            <strong>{stop.stop_name ?? stop.stop_id}</strong>
          </Popup>
        </CircleMarker>
      ))}
    </>
  )
}

export function LiveMap({ vehicles, routes, stops }: Props) {
  return (
    <MapContainer center={[43.70, -79.40]} zoom={11} className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {routes
        .filter((route) => route.shape_points.length > 1)
        .map((route) => (
          <Polyline key={route.route_id} positions={route.shape_points} pathOptions={{ color: '#2563eb', weight: 2 }} />
        ))}

      <MarkerClusterGroup chunkedLoading>
        {vehicles.map((vehicle) => (
          <Marker
            key={vehicle.vehicle_id}
            position={[vehicle.lat, vehicle.lon]}
            icon={vehicle.mode === 'streetcar' ? streetcarIcon : busIcon}
          >
            <Popup>
              <strong>{vehicle.route_short_name ?? vehicle.route_id ?? 'Unknown route'}</strong>
              <div>Vehicle: {vehicle.vehicle_id}</div>
              <div>Trip: {vehicle.trip_id ?? 'N/A'}</div>
              <div>Headsign: {vehicle.headsign ?? 'N/A'}</div>
              <div>Direction: {vehicle.direction_id ?? 'N/A'}</div>
              <div>Next stop: {vehicle.next_stop_name ?? vehicle.next_stop_id ?? 'N/A'}</div>
              <div>Delay: {vehicle.delay_seconds ?? 0}s</div>
              <div>Freshness: {vehicle.freshness_seconds ?? 'N/A'}s</div>
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>

      <ZoomAwareStops stops={stops} />
    </MapContainer>
  )
}
