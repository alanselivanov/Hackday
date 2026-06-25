import { useEffect } from 'react';
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import {
  IRTYSH_PILOT_POLYLINE,
  PILOT_MAP_BOUNDS,
  PILOT_MAP_CENTER,
  REPAIR_STATUS_COLORS,
  REPAIR_STATUS_LABELS,
} from '@/shared/config/constants';
import { Button } from '@/shared/ui/Button';
import styles from './PilotMap.module.css';

interface PilotMapProps {
  facilities: EnrichedHydroFacility[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

function FitBoundsControl() {
  const map = useMap();

  const fitToSegment = () => {
    map.fitBounds(PILOT_MAP_BOUNDS, { padding: [24, 24] });
  };

  useEffect(() => {
    fitToSegment();
  }, [map]);

  return (
    <div className={styles.controls}>
      <Button variant="secondary" size="sm" onClick={fitToSegment}>
        Fit to pilot segment
      </Button>
    </div>
  );
}

function FlyToSelected({
  selectedId,
  facilities,
}: {
  selectedId: number | null;
  facilities: EnrichedHydroFacility[];
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedId == null) return;
    const facility = facilities.find((f) => f.id === selectedId);
    if (!facility) return;
    map.flyTo([facility.location.lat, facility.location.lng], 12, { duration: 0.6 });
  }, [selectedId, facilities, map]);

  return null;
}

export function PilotMap({ facilities, selectedId, onSelect }: PilotMapProps) {
  return (
    <div className={styles.mapWrapper}>
      <MapContainer
        center={PILOT_MAP_CENTER}
        zoom={10}
        className={styles.map}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Polyline
          positions={IRTYSH_PILOT_POLYLINE}
          pathOptions={{ color: '#2563eb', weight: 4, opacity: 0.85 }}
        />

        {facilities.map((facility) => {
          const isSelected = facility.id === selectedId;
          const color = REPAIR_STATUS_COLORS[facility.repair_status];

          return (
            <CircleMarker
              key={facility.id}
              center={[facility.location.lat, facility.location.lng]}
              radius={isSelected ? 12 : 8}
              pathOptions={{
                color: isSelected ? '#0f172a' : color,
                fillColor: color,
                fillOpacity: isSelected ? 1 : 0.85,
                weight: isSelected ? 3 : 2,
              }}
              eventHandlers={{
                click: () => onSelect(facility.id),
              }}
            >
              <Popup>
                <div className={styles.popup}>
                  <strong>{facility.name}</strong>
                  <span>{facility.facility_type_label}</span>
                  <span>{facility.district}</span>
                  <span>
                    Status: {REPAIR_STATUS_LABELS[facility.repair_status]}
                  </span>
                  <span>Wear: {facility.wear_percentage.toFixed(1)}%</span>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        <FitBoundsControl />
        <FlyToSelected selectedId={selectedId} facilities={facilities} />
      </MapContainer>

      <div className={styles.legend}>
        <span className={styles.legendTitle}>Status legend</span>
        {Object.entries(REPAIR_STATUS_LABELS).map(([status, label]) => (
          <div key={status} className={styles.legendItem}>
            <span
              className={styles.legendDot}
              style={{
                backgroundColor:
                  REPAIR_STATUS_COLORS[status as keyof typeof REPAIR_STATUS_COLORS],
              }}
            />
            {label}
          </div>
        ))}
        <div className={styles.legendItem}>
          <span className={styles.legendLine} />
          Irtysh pilot segment
        </div>
      </div>
    </div>
  );
}
