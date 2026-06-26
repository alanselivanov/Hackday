import { useEffect } from 'react';
import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet';
import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import {
  PILOT_MAP_CENTER,
  REPAIR_STATUS_COLORS,
  REPAIR_STATUS_LABELS,
} from '@/shared/config/constants';
import { Button } from '@/shared/ui/Button';
import { getViewBounds } from '@/widgets/pilot-map/mapBounds';
import styles from './PilotMap.module.css';

interface PilotMapProps {
  facilities: EnrichedHydroFacility[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

function MapResizeTrigger({
  trigger,
  facilities,
}: {
  trigger: boolean;
  facilities: EnrichedHydroFacility[];
}) {
  const map = useMap();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      map.invalidateSize();
      map.fitBounds(getViewBounds(facilities), { padding: [24, 24] });
    }, 100);

    return () => window.clearTimeout(timer);
  }, [map, trigger, facilities]);

  return null;
}

function FitBoundsControl({
  facilities,
  onToggleFullscreen,
  isFullscreen,
}: {
  facilities: EnrichedHydroFacility[];
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
}) {
  const map = useMap();

  const fitToSegment = () => {
    map.fitBounds(getViewBounds(facilities), { padding: [24, 24] });
  };

  useEffect(() => {
    fitToSegment();
  }, [map, facilities]);

  return (
    <div className={styles.controls}>
      <Button variant="ghost" size="sm" onClick={fitToSegment}>
        К участку
      </Button>
      {onToggleFullscreen && (
        <Button variant="ghost" size="sm" onClick={onToggleFullscreen}>
          {isFullscreen ? 'Свернуть' : 'На весь экран'}
        </Button>
      )}
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

export function PilotMap({
  facilities,
  selectedId,
  onSelect,
  isFullscreen = false,
  onToggleFullscreen,
}: PilotMapProps) {
  return (
    <div className={isFullscreen ? `${styles.mapWrapper} ${styles.fullscreen}` : styles.mapWrapper}>
      <MapContainer
        center={PILOT_MAP_CENTER}
        zoom={10}
        className={styles.map}
        scrollWheelZoom
      >
        <TileLayer
          attribution='Tiles &copy; Esri, Maxar, Earthstar Geographics'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />

        {facilities.map((facility) => {
          const isSelected = facility.id === selectedId;
          const color = facility.repair_status
            ? REPAIR_STATUS_COLORS[facility.repair_status]
            : '#718096';

          return (
            <CircleMarker
              key={facility.id}
              center={[facility.location.lat, facility.location.lng]}
              radius={isSelected ? 12 : 8}
              pathOptions={{
                color: isSelected ? '#1a202c' : color,
                fillColor: color,
                fillOpacity: isSelected ? 1 : 0.85,
                weight: isSelected ? 3 : 2,
              }}
              eventHandlers={{
                click: () => onSelect(facility.id),
              }}
            >
              <Tooltip
                direction="top"
                offset={[0, -8]}
                opacity={1}
                permanent={!isFullscreen}
                className={styles.markerLabel}
              >
                {facility.map_label ?? `Объект ${facility.id}`}
              </Tooltip>
              <Popup>
                <div className={styles.popup}>
                  <strong>{facility.name}</strong>
                  <span>{facility.facility_type_label}</span>
                  <span>{facility.district}</span>
                  <span>Статус: {facility.repair_status_label ?? '—'}</span>
                  <span>Износ: {facility.wear_percentage.toFixed(1)}%</span>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        <FitBoundsControl
          facilities={facilities}
          onToggleFullscreen={onToggleFullscreen}
          isFullscreen={isFullscreen}
        />
        <FlyToSelected selectedId={selectedId} facilities={facilities} />
        <MapResizeTrigger trigger={isFullscreen} facilities={facilities} />
      </MapContainer>

      <div className={styles.legend}>
        <span className={styles.legendTitle}>Состояние объекта</span>
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
      </div>

      {isFullscreen && selectedId != null && (
        <div className={styles.fullscreenHint}>
          Нажмите Esc или «Свернуть», чтобы вернуться к общему виду
        </div>
      )}
    </div>
  );
}
