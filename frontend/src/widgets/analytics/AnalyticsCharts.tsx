import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { EnrichedHydroFacility, RepairStatus } from '@/entities/facility/model/types';
import {
  FACILITY_TYPE_LABELS,
  REPAIR_STATUS_COLORS,
  REPAIR_STATUS_LABELS,
} from '@/shared/config/constants';
import { Card } from '@/shared/ui/Card';
import styles from './AnalyticsCharts.module.css';

interface AnalyticsChartsProps {
  facilities: EnrichedHydroFacility[];
}

function buildStatusData(facilities: EnrichedHydroFacility[]) {
  const counts: Record<RepairStatus, number> = {
    normal: 0,
    inspection_required: 0,
    repair_required: 0,
    critical: 0,
  };

  facilities.forEach((f) => {
    counts[f.repair_status] += 1;
  });

  return (Object.keys(counts) as RepairStatus[]).map((status) => ({
    name: REPAIR_STATUS_LABELS[status],
    status,
    value: counts[status],
    fill: REPAIR_STATUS_COLORS[status],
  }));
}

function buildTypeData(facilities: EnrichedHydroFacility[]) {
  const counts = new Map<string, number>();

  facilities.forEach((f) => {
    counts.set(f.facility_type_label, (counts.get(f.facility_type_label) ?? 0) + 1);
  });

  return Array.from(counts.entries()).map(([name, value]) => ({ name, value }));
}

function buildDistrictData(facilities: EnrichedHydroFacility[]) {
  const counts = new Map<string, number>();

  facilities.forEach((f) => {
    counts.set(f.district, (counts.get(f.district) ?? 0) + 1);
  });

  return Array.from(counts.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
}

const TYPE_COLORS = ['#0d9488', '#0891b2', '#0284c7', '#6366f1', '#7c3aed', '#db2777'];
const DISTRICT_COLORS = ['#14b8a6', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'];

export function AnalyticsCharts({ facilities }: AnalyticsChartsProps) {
  const statusData = buildStatusData(facilities);
  const typeData = buildTypeData(facilities);
  const districtData = buildDistrictData(facilities);

  return (
    <div className={styles.grid}>
      <Card className={styles.chartCard}>
        <h3 className={styles.title}>By repair status</h3>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={statusData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={90}
              paddingAngle={2}
            >
              {statusData.map((entry) => (
                <Cell key={entry.status} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </Card>

      <Card className={styles.chartCard}>
        <h3 className={styles.title}>By facility type</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={typeData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              interval={0}
              angle={-25}
              textAnchor="end"
              height={60}
            />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {typeData.map((_, index) => (
                <Cell key={index} fill={TYPE_COLORS[index % TYPE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className={styles.chartCard}>
        <h3 className={styles.title}>By district</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={districtData} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="name"
              width={110}
              tick={{ fontSize: 11 }}
            />
            <Tooltip />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {districtData.map((_, index) => (
                <Cell key={index} fill={DISTRICT_COLORS[index % DISTRICT_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

/** Export for reference in type labels if needed */
export { FACILITY_TYPE_LABELS };
