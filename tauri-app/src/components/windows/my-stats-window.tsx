import { useEffect, useState } from "react";
import { useSyncStore } from "@/stores/sync-store";
import { Clock, BarChart3, Award, TrendingUp } from "lucide-react";

interface StatsData {
  summary: {
    total_encounters: number;
    avg_duration: number | null;
    total_modules_completed: number;
    total_edits: number;
  };
  recentEncounters: Array<{
    id: string;
    case_title?: string;
    total_duration_secs?: number;
    modules_completed?: number;
    started_at?: string;
  }>;
  submissions: Array<{
    id: string;
    status: string;
    grade?: number;
    case_title?: string;
    session_title?: string;
    submitted_at?: string;
  }>;
  moduleBreakdown: Array<{
    module_id: string;
    total_time: number;
    avg_time: number;
    uses: number;
  }>;
}

/**
 * Ventana "Mis Estadísticas" para el estudiante
 */
export function MyStatsWindow() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const getMyStats = useSyncStore((s) => s.getMyStats);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    setLoading(true);
    try {
      const result = (await getMyStats()) as StatsData;
      setStats(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function formatDuration(secs: number | null): string {
    if (!secs) return "—";
    if (secs < 60) return `${secs}s`;
    if (secs < 3600) return `${Math.floor(secs / 60)}m ${secs % 60}s`;
    return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center ls-bg ls-text-muted">
        Cargando estadísticas...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center ls-bg p-4">
        <p className="text-red-400 mb-3 text-sm">{error}</p>
        <button onClick={loadStats} className="ls-btn-primary px-4 py-2 rounded text-sm">
          Reintentar
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="h-full overflow-auto ls-bg p-4">
      <h2 className="text-lg font-semibold ls-text mb-4">Mis Estadísticas</h2>

      {/* Resumen */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="ls-card border ls-border rounded p-3 text-center">
          <BarChart3 className="w-5 h-5 mx-auto mb-1 text-indigo-400" />
          <div className="text-xl font-bold ls-text">{stats.summary.total_encounters}</div>
          <div className="text-xs ls-text-muted">Encuentros</div>
        </div>
        <div className="ls-card border ls-border rounded p-3 text-center">
          <Clock className="w-5 h-5 mx-auto mb-1 text-emerald-400" />
          <div className="text-xl font-bold ls-text">
            {formatDuration(stats.summary.avg_duration ? Math.round(stats.summary.avg_duration) : null)}
          </div>
          <div className="text-xs ls-text-muted">Duración prom.</div>
        </div>
        <div className="ls-card border ls-border rounded p-3 text-center">
          <TrendingUp className="w-5 h-5 mx-auto mb-1 text-amber-400" />
          <div className="text-xl font-bold ls-text">{stats.summary.total_modules_completed}</div>
          <div className="text-xs ls-text-muted">Módulos completados</div>
        </div>
        <div className="ls-card border ls-border rounded p-3 text-center">
          <Award className="w-5 h-5 mx-auto mb-1 text-pink-400" />
          <div className="text-xl font-bold ls-text">{stats.summary.total_edits}</div>
          <div className="text-xs ls-text-muted">Ediciones totales</div>
        </div>
      </div>

      {/* Entregas */}
      {stats.submissions.length > 0 && (
        <div className="mb-5">
          <h3 className="text-sm font-medium ls-text mb-2">Entregas recientes</h3>
          <div className="space-y-1">
            {stats.submissions.slice(0, 10).map((s) => (
              <div key={s.id} className="flex items-center gap-2 p-2 rounded ls-card border ls-border text-sm">
                <span className="flex-1 ls-text">{s.case_title ?? "Caso"}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  s.status === "reviewed" ? "bg-green-900/30 text-green-400" :
                  s.status === "submitted" ? "bg-blue-900/30 text-blue-400" :
                  s.status === "returned" ? "bg-yellow-900/30 text-yellow-400" :
                  "bg-gray-900/30 text-gray-400"
                }`}>
                  {s.status}
                </span>
                {s.grade != null && (
                  <span className="text-xs font-bold text-indigo-400">{s.grade.toFixed(1)}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tiempo por módulo */}
      {stats.moduleBreakdown.length > 0 && (
        <div>
          <h3 className="text-sm font-medium ls-text mb-2">Tiempo por módulo</h3>
          <div className="space-y-2">
            {stats.moduleBreakdown.map((m) => {
              const maxTime = Math.max(...stats.moduleBreakdown.map((x) => x.total_time));
              const pct = maxTime > 0 ? (m.total_time / maxTime) * 100 : 0;
              return (
                <div key={m.module_id}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="ls-text">{m.module_id}</span>
                    <span className="ls-text-muted">{formatDuration(Math.round(m.avg_time))} prom.</span>
                  </div>
                  <div className="h-2 rounded bg-gray-800">
                    <div
                      className="h-full rounded bg-indigo-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
