import { useState, useEffect, useMemo, useCallback } from "react";
import { useLarissaStore, type CaseProfile, type AgendaItem } from "@/stores/larissa-store";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { useUIStore } from "@/stores/ui-store";
import { WINDOW_SIZES } from "@/components/layout/desktop-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ClipboardPen,
  FolderOpen,
  CalendarDays,
  Search,
  RefreshCw,
  User,
  Loader2,
  ExternalLink,
  FlaskConical,
  ArrowLeft,
  Clock,
  UserPlus,
  ChevronRight,
  Trash2,
  Pencil,
  Plus,
} from "lucide-react";

// ─── Helpers ─────────────────────────────────────────

/** Mapeo de store key (camelCase) → nombre legible */
const MODULE_NAMES: Record<string, string> = {
  audiometry: "Audiometría",
  tuningFork: "Acumetría",
  logoaudiometry: "Logoaudiometría",
  supraliminal: "Supraliminal",
  impedance: "Impedanciometría",
  oae: "Emisiones Otoacústicas",
  abr: "Potenciales Evocados",
  electrocochleo: "Electrococleografía",
  hearingAids: "Audífonos",
  oct: "OCT",
  visualField: "Campo Visual",
  cornealTopography: "Topografía Corneal",
  retinography: "Retinografía",
  scheimpflug: "Scheimpflug",
  vng: "VNG",
  vhit: "vHIT",
};

/** Mapeo de store key → ventana del simulador */
const MODULE_WINDOW_MAP: Record<string, { id: string; title: string; component: string } | null> = {
  audiometry: { id: "audiometer", title: "Audiómetro", component: "audiometer" },
  impedance: { id: "impedance", title: "Impedanciómetro", component: "impedance" },
  oct: { id: "oct", title: "OCT", component: "oct" },
  visualField: { id: "perimetry", title: "Campo Visual", component: "perimetry" },
  retinography: { id: "retinography", title: "Retinografía", component: "retinography" },
  cornealTopography: { id: "corneal-topography", title: "Topografía Corneal", component: "corneal-topography" },
  scheimpflug: { id: "scheimpflug", title: "Scheimpflug", component: "scheimpflug" },
  vng: { id: "vng", title: "VNG", component: "vng" },
  vhit: { id: "vhit", title: "vHIT", component: "vhit" },
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "text-emerald-400 border-emerald-500/30",
  medium: "text-amber-400 border-amber-500/30",
  hard: "text-red-400 border-red-500/30",
};

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Fácil",
  medium: "Medio",
  hard: "Difícil",
};

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/** Genera resumen breve para un módulo */
function getModuleSummary(storeKey: string, data: Record<string, unknown>): string | null {
  if (storeKey === "audiometry") {
    const tipo = data.tipoPerdida as Record<string, string> | undefined;
    if (tipo) {
      const parts: string[] = [];
      if (tipo.od) parts.push(`OD: ${tipo.od}`);
      if (tipo.oi) parts.push(`OI: ${tipo.oi}`);
      if (parts.length > 0) return parts.join(", ");
    }
    return null;
  }
  if (storeKey === "tuningFork") {
    const rinne = data.rinne as Record<string, string> | undefined;
    const weber = data.weber as string | undefined;
    const parts: string[] = [];
    if (rinne) {
      if (rinne.od) parts.push(`Rinne OD: ${rinne.od}`);
      if (rinne.oi) parts.push(`Rinne OI: ${rinne.oi}`);
    }
    if (weber) parts.push(`Weber: ${weber}`);
    return parts.length > 0 ? parts.join(", ") : null;
  }
  if (storeKey === "impedance") {
    const tipo = data.tipoTimpanograma as Record<string, string> | undefined;
    if (tipo) {
      const parts: string[] = [];
      if (tipo.od) parts.push(`OD: ${tipo.od}`);
      if (tipo.oi) parts.push(`OI: ${tipo.oi}`);
      if (parts.length > 0) return parts.join(", ");
    }
  }
  const fieldCount = Object.keys(data).length;
  return `${fieldCount} campos registrados`;
}

// ─── Sub-componentes ─────────────────────────────────

function FichaBaseTab({ profile }: { profile: CaseProfile }) {
  const identity = (profile.core?.identity ?? {}) as Record<string, unknown>;
  const personality = (profile.core?.personality ?? {}) as Record<string, unknown>;
  const history = (profile.core?.clinicalHistory ?? {}) as Record<string, unknown>;

  return (
    <ScrollArea className="flex-1 min-h-0">
      <div className="p-4 space-y-3">
        {/* Datos Personales */}
        <FieldSection title="Datos Personales">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
            <FieldPair
              label="Nombre"
              value={[identity.firstName, identity.lastName].filter(Boolean).join(" ") || null}
            />
            <FieldPair label="Nombre clínico" value={identity.displayName} />
            <FieldPair label="RUN/ID" value={identity.documentId} />
            <FieldPair
              label="Edad"
              value={identity.age != null ? `${identity.age} años` : null}
            />
            <FieldPair label="Género" value={identity.gender} />
            <FieldPair label="Teléfono" value={identity.phone} />
            <FieldPair label="Email" value={identity.email} />
            <FieldPair
              label="Dirección"
              value={[identity.address, identity.city].filter(Boolean).join(", ") || null}
            />
            <FieldPair label="Ocupación" value={identity.occupation} />
            <FieldPair label="Previsión" value={identity.healthInsurance} />
            <FieldPair label="Derivado por" value={identity.referredBy} />
            <FieldPair label="Notas" value={identity.notes} />
          </div>
        </FieldSection>

        {/* Personalidad */}
        {Object.keys(personality).length > 0 && (
          <FieldSection title="Personalidad">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
              <FieldPair label="Tipo" value={personality.personalityType} />
              <FieldPair label="Estilo comunicación" value={personality.communicationStyle} />
              <FieldPair label="Tono" value={personality.toneOfVoice} />
              <FieldPair label="Cooperación" value={personality.cooperationLevel} />
            </div>
          </FieldSection>
        )}

        {/* Historia Clínica */}
        {Object.keys(history).length > 0 && (
          <FieldSection title="Historia Clínica">
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                <FieldPair label="Motivo de consulta" value={history.mainComplaint} />
                <FieldPair label="Tiempo de evolución" value={history.evolutionTime} />
                <FieldPair label="Severidad" value={history.severity} />
                <FieldPair
                  label="Antecedentes"
                  value={
                    Array.isArray(history.medicalHistory) && history.medicalHistory.length > 0
                      ? history.medicalHistory.join(", ")
                      : null
                  }
                />
                <FieldPair label="Antecedentes quirúrgicos" value={history.surgicalHistory} />
                <FieldPair label="Historia familiar" value={history.familyHistory} />
                <FieldPair label="Medicamentos" value={history.medications} />
                <FieldPair label="Alergias" value={history.allergies} />
                <FieldPair
                  label="Exposición a ruido"
                  value={
                    history.noiseExposure
                      ? `${history.noiseExposure}${history.noiseYears ? ` (${history.noiseYears} años)` : ""}`
                      : null
                  }
                />
                <FieldPair
                  label="Protección auditiva"
                  value={
                    history.hearingProtection != null
                      ? history.hearingProtection
                        ? "Sí"
                        : "No"
                      : null
                  }
                />
                <FieldPair
                  label="Tinnitus"
                  value={
                    history.tinnitus != null
                      ? history.tinnitus
                        ? "Sí"
                        : "No"
                      : null
                  }
                />
                <FieldPair
                  label="Vértigo"
                  value={
                    history.vertigo != null
                      ? history.vertigo
                        ? "Sí"
                        : "No"
                      : null
                  }
                />
              </div>

              {/* Descripción del motivo — ancho completo */}
              {history.complaintDescription && (
                <div>
                  <span className="text-xs ls-text-muted">Descripción:</span>
                  <p className="text-xs ls-text2 whitespace-pre-wrap mt-0.5">
                    {String(history.complaintDescription)}
                  </p>
                </div>
              )}

              {/* Descripción tinnitus */}
              {history.tinnitus && history.tinnitusDescription && (
                <div>
                  <span className="text-xs ls-text-muted">Descripción del tinnitus:</span>
                  <p className="text-xs ls-text2 whitespace-pre-wrap mt-0.5">
                    {String(history.tinnitusDescription)}
                  </p>
                </div>
              )}

              {/* Descripción vértigo */}
              {history.vertigo && history.vertigoDescription && (
                <div>
                  <span className="text-xs ls-text-muted">Descripción del vértigo:</span>
                  <p className="text-xs ls-text2 whitespace-pre-wrap mt-0.5">
                    {String(history.vertigoDescription)}
                  </p>
                </div>
              )}
            </div>
          </FieldSection>
        )}
      </div>
    </ScrollArea>
  );
}

function ExamenesTab({ profile }: { profile: CaseProfile }) {
  const openWindow = useUIStore((s) => s.openWindow);
  const modules = profile.modules ?? {};

  const activeModules = useMemo(
    () =>
      Object.entries(modules).filter(
        ([, data]) => data && typeof data === "object" && Object.keys(data).length > 0,
      ),
    [modules],
  );

  if (activeModules.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
        <FlaskConical className="h-10 w-10 ls-text-muted opacity-30" />
        <p className="text-xs ls-text-muted">No hay resultados de exámenes</p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 min-h-0">
      <div className="p-4 space-y-3">
        {activeModules.map(([storeKey, data]) => {
          const name = MODULE_NAMES[storeKey] ?? storeKey;
          const summary = getModuleSummary(storeKey, data);
          const windowInfo = MODULE_WINDOW_MAP[storeKey];

          return (
            <div key={storeKey} className="rounded-lg border ls-border ls-bg-input p-3">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span className="text-xs font-medium ls-text">{name}</span>
                  </div>
                  {summary && (
                    <p className="text-[10px] ls-text-muted mt-1 ml-5.5 truncate">{summary}</p>
                  )}
                </div>
                {windowInfo && (
                  <Button
                    size="sm"
                    className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500 h-6 px-2 text-[10px]"
                    onClick={() =>
                      openWindow(
                        windowInfo.id,
                        windowInfo.title,
                        windowInfo.component,
                        WINDOW_SIZES[windowInfo.id],
                      )
                    }
                  >
                    <ExternalLink className="h-3 w-3" />
                    Abrir
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

function FieldSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border ls-border ls-bg-input p-3">
      <h4 className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted mb-2">
        {title}
      </h4>
      {children}
    </div>
  );
}

function FieldPair({ label, value }: { label: string; value: unknown }) {
  if (value == null || value === "" || (Array.isArray(value) && value.length === 0)) return null;
  return (
    <>
      <span className="ls-text-muted">{label}:</span>
      <span className="ls-text2">{String(value)}</span>
    </>
  );
}

// ─── Main Component ──────────────────────────────────

export function LarissaWindow() {
  const {
    mainView,
    setMainView,
    patients,
    patientsLoading,
    searchQuery,
    selectedPatientId,
    patientProfile,
    patientLoading,
    patientTab,
    fetchPatients,
    selectPatient,
    setSearchQuery,
    setPatientTab,
  } = useLarissaStore();

  const openWindow = useUIStore((s) => s.openWindow);

  // Cargar pacientes al montar
  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  // Filtrar pacientes por búsqueda
  const filteredPatients = useMemo(() => {
    if (!searchQuery.trim()) return patients;
    const q = searchQuery.toLowerCase();
    return patients.filter((p) => p.title.toLowerCase().includes(q));
  }, [patients, searchQuery]);

  // Extraer datos del perfil seleccionado
  const identity = (patientProfile?.core?.identity ?? {}) as Record<string, unknown>;
  const displayName = (identity.displayName as string) ??
    [identity.firstName, identity.lastName].filter(Boolean).join(" ") ??
    "";
  const initials = getInitials(displayName || "?");

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* ─── Header ─── */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
        <ClipboardPen className="h-4 w-4 text-cyan-400" />
        <span className="text-xs font-medium ls-text2">Larissa</span>
        <div className="ml-4 flex items-center gap-0.5">
          <button
            onClick={() => setMainView("fichas")}
            className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${
              mainView === "fichas"
                ? "bg-cyan-500/15 text-cyan-400"
                : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            <FolderOpen className="inline h-3 w-3 mr-1" />
            Fichas Clínicas
          </button>
          <button
            onClick={() => setMainView("agenda")}
            className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${
              mainView === "agenda"
                ? "bg-cyan-500/15 text-cyan-400"
                : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            <CalendarDays className="inline h-3 w-3 mr-1" />
            Agenda
          </button>
        </div>
      </div>

      {/* ─── Content ─── */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {mainView === "fichas" ? (
          <>
            {/* ─── Sidebar: lista de pacientes ─── */}
            <div className="w-[280px] shrink-0 flex flex-col border-r ls-border overflow-hidden">
              {/* Sidebar header */}
              <div className="flex items-center justify-between px-3 py-2 shrink-0">
                <span className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted">
                  Pacientes
                </span>
                <button
                  onClick={() => fetchPatients()}
                  className="rounded p-1 ls-text-muted hover:ls-text2 hover:ls-bg-input transition"
                  title="Recargar pacientes"
                >
                  <RefreshCw className={`h-3 w-3 ${patientsLoading ? "animate-spin" : ""}`} />
                </button>
              </div>

              {/* Search */}
              <div className="px-3 pb-2 shrink-0">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 ls-text-muted" />
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar paciente..."
                    className="h-7 pl-7 text-xs"
                  />
                </div>
              </div>

              {/* Patient list */}
              <ScrollArea className="flex-1 min-h-0">
                <div className="px-2 pb-2">
                  {patientsLoading && patients.length === 0 ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-4 w-4 animate-spin ls-text-muted" />
                    </div>
                  ) : filteredPatients.length === 0 ? (
                    <p className="text-center text-[10px] ls-text-muted py-8">
                      {searchQuery ? "Sin resultados" : "No hay pacientes"}
                    </p>
                  ) : (
                    filteredPatients.map((patient) => (
                      <button
                        key={patient.id}
                        onClick={() => selectPatient(patient.id)}
                        className={`w-full rounded-md px-2.5 py-2 text-left transition mb-0.5 ${
                          selectedPatientId === patient.id
                            ? "bg-cyan-500/10"
                            : "hover:ls-bg-input"
                        }`}
                      >
                        <div className="text-xs font-medium ls-text truncate">
                          {patient.title}
                        </div>
                        <div className="flex items-center gap-1.5 mt-1">
                          {patient.difficulty && (
                            <Badge
                              variant="outline"
                              className={`text-[9px] px-1 py-0 ${
                                DIFFICULTY_COLORS[patient.difficulty] ?? ""
                              }`}
                            >
                              {DIFFICULTY_LABELS[patient.difficulty] ?? patient.difficulty}
                            </Badge>
                          )}
                          {patient.tags && (
                            <span className="text-[10px] ls-text-muted truncate">
                              {patient.tags.split(",").slice(0, 3).join(", ")}
                            </span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>

            {/* ─── Panel: detalle del paciente ─── */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              {!selectedPatientId ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                  <User className="h-10 w-10 ls-text-muted opacity-30" />
                  <p className="text-xs ls-text-muted">Selecciona un paciente</p>
                </div>
              ) : patientLoading ? (
                <div className="flex h-full items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
                </div>
              ) : patientProfile ? (
                <>
                  {/* Patient header */}
                  <div className="border-b ls-border px-4 py-3 shrink-0">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/15 text-cyan-400 text-sm font-bold">
                        {initials}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold ls-text truncate">{displayName}</h3>
                        <div className="flex items-center gap-2 text-xs ls-text-muted">
                          {identity.gender && <span>{String(identity.gender)}</span>}
                          {identity.age != null && <span>{String(identity.age)} años</span>}
                          {identity.healthInsurance && (
                            <span>{String(identity.healthInsurance)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sub-tabs */}
                  <div className="flex items-center gap-1 border-b ls-border px-4 py-1.5 shrink-0">
                    <button
                      onClick={() => setPatientTab("ficha-base")}
                      className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${
                        patientTab === "ficha-base"
                          ? "bg-cyan-500/15 text-cyan-400"
                          : "ls-text-muted hover:ls-bg-input"
                      }`}
                    >
                      Ficha Base
                    </button>
                    <button
                      onClick={() => setPatientTab("examenes")}
                      className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${
                        patientTab === "examenes"
                          ? "bg-cyan-500/15 text-cyan-400"
                          : "ls-text-muted hover:ls-bg-input"
                      }`}
                    >
                      Exámenes
                    </button>
                  </div>

                  {/* Tab content */}
                  {patientTab === "ficha-base" ? (
                    <FichaBaseTab profile={patientProfile} />
                  ) : (
                    <ExamenesTab profile={patientProfile} />
                  )}
                </>
              ) : (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                  <User className="h-10 w-10 ls-text-muted opacity-30" />
                  <p className="text-xs ls-text-muted">No se pudo cargar el perfil</p>
                </div>
              )}
            </div>
          </>
        ) : (
          /* ─── Vista Agenda ─── */
          <AgendaView />
        )}
      </div>

      {/* ─── Status bar ─── */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted shrink-0">
        {mainView === "fichas" && <span>{patients.length} pacientes</span>}
        {mainView === "fichas" && selectedPatientId && patientProfile && <span>{displayName}</span>}
        {mainView === "agenda" && <span>Larissa — Agenda</span>}
      </div>
    </div>
  );
}

// ─── Vista Agenda ───────────────────────────────────

function AgendaView() {
  const agendaSessions = useLarissaStore((s) => s.agendaSessions);
  const agendaSessionsLoading = useLarissaStore((s) => s.agendaSessionsLoading);
  const agendaView = useLarissaStore((s) => s.agendaView);
  const selectedAgendaSessionId = useLarissaStore((s) => s.selectedAgendaSessionId);
  const agendaItems = useLarissaStore((s) => s.agendaItems);
  const agendaLoading = useLarissaStore((s) => s.agendaLoading);
  const patients = useLarissaStore((s) => s.patients);
  const fetchAgendaSessions = useLarissaStore((s) => s.fetchAgendaSessions);
  const selectAgendaSession = useLarissaStore((s) => s.selectAgendaSession);
  const assignPatientToSlot = useLarissaStore((s) => s.assignPatientToSlot);
  const deleteAgendaSession = useLarissaStore((s) => s.deleteAgendaSession);
  const fetchPatients = useLarissaStore((s) => s.fetchPatients);
  const role = useAuthStore((s) => s.role);
  const [deleting, setDeleting] = useState<string | null>(null);

  const canDelete = role === "admin" || role === "docente";

  useEffect(() => {
    fetchAgendaSessions();
    fetchPatients();
  }, [fetchAgendaSessions, fetchPatients]);

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("¿Eliminar esta agenda? Los bloques se cancelarán.")) return;
    setDeleting(sessionId);
    try {
      await deleteAgendaSession(sessionId);
      toast.success("Agenda eliminada");
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setDeleting(null);
    }
  };

  const selectedSession = agendaSessions.find((s) => s.id === selectedAgendaSessionId);

  // Hooks para vista detalle — DEBEN estar antes de cualquier return
  const groupedByDate = useMemo(() => {
    const groups: Record<string, Array<AgendaItem & { index: number }>> = {};
    agendaItems.forEach((item, i) => {
      const key = item.scheduled_date;
      if (!groups[key]) groups[key] = [];
      groups[key].push({ ...item, index: i });
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [agendaItems]);

  const DAY_NAMES_AGENDA = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];
  const HOUR_HEIGHT_AGENDA = 80;
  const HOURS_AGENDA = Array.from({ length: 13 }, (_, i) => i + 7);

  // ─── Lista de agendas ───
  if (agendaView === "list") {
    return (
      <div className="flex h-full w-full flex-col overflow-hidden">
        <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
          <span className="text-xs font-medium ls-text2">Agendas</span>
          <Button size="icon-xs" variant="ghost" onClick={() => fetchAgendaSessions()} className="ml-auto ls-text-muted hover:ls-text">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
        <ScrollArea className="flex-1 min-h-0">
          {agendaSessionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
            </div>
          ) : agendaSessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <CalendarDays className="h-10 w-10 ls-text-muted opacity-30" />
              <div>
                <p className="text-xs ls-text2">No hay agendas configuradas</p>
                <p className="text-[10px] ls-text-muted mt-1">Crea una actividad desde el Panel Docente</p>
              </div>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {agendaSessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectAgendaSession(s.id)}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition hover:ls-bg-input group"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">
                    <CalendarDays className="h-4.5 w-4.5 text-cyan-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-medium ls-text2 truncate block">{s.title}</span>
                    <div className="flex items-center gap-2 text-[10px] ls-text-muted">
                      {s.scheduled_date && <span>{s.scheduled_date}</span>}
                      <span>{s.block_count} bloques</span>
                      <Badge variant="outline" className={`text-[8px] px-1 py-0 ${
                        s.status === "active" ? "text-emerald-400 bg-emerald-500/10" :
                        s.status === "approved" ? "text-sky-400 bg-sky-500/10" :
                        "text-zinc-400 bg-zinc-500/10"
                      }`}>{s.status}</Badge>
                    </div>
                  </div>
                  {canDelete && (
                    <button
                      onClick={(e) => handleDelete(s.id, e)}
                      disabled={deleting === s.id}
                      className="shrink-0 text-red-400/0 group-hover:text-red-400/60 hover:!text-red-400 transition"
                    >
                      {deleting === s.id
                        ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        : <Trash2 className="h-3.5 w-3.5" />
                      }
                    </button>
                  )}
                  <ChevronRight className="h-4 w-4 ls-text-muted shrink-0" />
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    );
  }

  // ─── Detalle de agenda: calendario con slots ───

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
        <Button size="xs" variant="ghost" onClick={() => selectAgendaSession(null)} className="gap-1 ls-text-muted hover:ls-text">
          <ArrowLeft className="h-3 w-3" />Agendas
        </Button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <span className="text-xs font-medium ls-text2">{selectedSession?.title ?? "Agenda"}</span>
        <Badge variant="outline" className="text-[9px] ls-border ls-text-muted ml-auto">
          {agendaItems.length} bloques
        </Badge>
      </div>

      {agendaLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
        </div>
      ) : agendaItems.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3">
          <CalendarDays className="h-10 w-10 ls-text-muted opacity-30" />
          <p className="text-xs ls-text-muted">Esta agenda no tiene bloques configurados</p>
        </div>
      ) : (
        <div className="flex-1 overflow-auto">
          <div className="flex min-w-0">
            {/* Columna de horas */}
            <div className="w-11 shrink-0 sticky left-0 ls-bg" style={{ zIndex: 2 }}>
              <div className="h-8" />
              {HOURS_AGENDA.map((hour) => (
                <div key={hour} className="flex items-start justify-end pr-1.5 -mt-1.5" style={{ height: HOUR_HEIGHT_AGENDA }}>
                  <span className="text-[10px] ls-text-muted">{String(hour).padStart(2, "0")}:00</span>
                </div>
              ))}
            </div>

            {/* Columnas por día */}
            {groupedByDate.map(([date, items]) => {
              const d = new Date(date + "T00:00:00");
              return (
                <div key={date} className="flex-1 min-w-[100px] border-l ls-border/50">
                  <div className="sticky top-0 h-8 flex flex-col items-center justify-center border-b ls-border ls-bg" style={{ zIndex: 1 }}>
                    <span className="text-[9px] font-bold uppercase ls-text-muted">{DAY_NAMES_AGENDA[d.getDay()]}</span>
                    <span className="text-[11px] font-medium leading-none ls-text2">{d.getDate()}</span>
                  </div>
                  <div className="relative" style={{ height: HOURS_AGENDA.length * HOUR_HEIGHT_AGENDA }}>
                    {HOURS_AGENDA.map((hour) => (
                      <div key={hour} className="absolute left-0 right-0 border-t ls-border/30" style={{ top: (hour - 7) * HOUR_HEIGHT_AGENDA, height: HOUR_HEIGHT_AGENDA }} />
                    ))}
                    {items.sort((a, b) => a.scheduled_time.localeCompare(b.scheduled_time)).map((item) => {
                      const [h, m] = item.scheduled_time.split(":").map(Number);
                      const top = ((h - 7) * 60 + m) / 60 * HOUR_HEIGHT_AGENDA;
                      const height = Math.max((item.duration_minutes / 60) * HOUR_HEIGHT_AGENDA, 28);
                      const isEmpty = !item.patient_name || item.patient_name === "—" || item.patient_name === item.patient_notes;

                      return (
                        <AgendaSlot
                          key={item.id}
                          item={item}
                          top={top}
                          height={height}
                          isEmpty={isEmpty}
                          patients={patients}
                          onAssign={assignPatientToSlot}
                          canEdit={canDelete}
                        />
                      );
                    })}
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

function AgendaSlot({
  item, top, height, isEmpty, patients, onAssign, canEdit,
}: {
  item: AgendaItem;
  top: number;
  height: number;
  isEmpty: boolean;
  patients: Array<{ id: string; title: string }>;
  onAssign: (id: string, name: string, caseId?: string) => Promise<void>;
  canEdit: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const openWindow = useUIStore((s) => s.openWindow);

  const filtered = useMemo(() => {
    if (!search.trim()) return patients;
    const q = search.toLowerCase();
    return patients.filter((p) => p.title.toLowerCase().includes(q));
  }, [patients, search]);

  const procedureName = item.patient_notes || item.procedure_name || "";

  return (
    <>
      <div
        onClick={() => setOpen(true)}
        className={`absolute left-0.5 right-0.5 rounded-md border px-1.5 py-1 cursor-pointer transition ${
          isEmpty
            ? "border-dashed ls-border bg-[var(--ls-input-bg)] hover:border-cyan-500/40"
            : "border-cyan-500/30 bg-cyan-500/20 hover:bg-cyan-500/30"
        }`}
        style={{ top, height }}
      >
        {isEmpty ? (
          <div className="flex items-center gap-1 h-full">
            <span className="text-[10px] ls-text-muted">{item.scheduled_time}</span>
            <span className="text-[10px] ls-text-muted truncate">{procedureName}</span>
          </div>
        ) : (
          <>
            <span className="text-[10px] font-semibold text-cyan-300 truncate block">
              {item.patient_name.split(/\s*[—–]\s*/)[0].trim()}
            </span>
            {height > 30 && (
              <span className="text-[9px] text-cyan-400/50 leading-none block">
                {item.scheduled_time} · {item.duration_minutes}m
              </span>
            )}
          </>
        )}
      </div>

      {/* Panel lateral al hacer click */}
      {open && (
        <div
          className="fixed inset-0"
          style={{ zIndex: 9998 }}
          onClick={() => setOpen(false)}
        >
          <div
            className="absolute rounded-lg border ls-border ls-bg shadow-xl p-3 w-64"
            style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)", zIndex: 9999 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="text-xs font-medium ls-text2">{item.scheduled_time} — {item.duration_minutes} min</div>
                {procedureName && <div className="text-[10px] ls-text-muted">{procedureName}</div>}
              </div>
              <button onClick={() => setOpen(false)} className="ls-text-muted hover:ls-text">
                <span className="text-lg leading-none">&times;</span>
              </button>
            </div>

            {/* Paciente asignado */}
            {!isEmpty && (
              <div className="rounded-md border ls-border p-2 mb-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-cyan-500/15 text-cyan-400 text-[10px] font-bold">
                    {item.patient_name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-medium ls-text2 truncate block">{item.patient_name}</span>
                  </div>
                  {canEdit && (
                    <button
                      onClick={() => setSearch("")}
                      className="text-[10px] text-cyan-400 hover:text-cyan-300"
                      title="Cambiar paciente"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Buscador + lista (solo si puede editar) */}
            {canEdit && (
              <>
                <div className="relative mb-1.5">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 ls-text-muted" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Buscar paciente..."
                    className="w-full h-7 rounded-md border pl-7 pr-2 text-[11px] ls-border ls-bg-input ls-text outline-none"
                    autoFocus
                  />
                </div>
                <div className="max-h-36 overflow-y-auto space-y-0.5">
                  {filtered.length === 0 ? (
                    <p className="text-[10px] ls-text-muted py-2 text-center">Sin resultados</p>
                  ) : (
                    filtered.map((p) => {
                      // Extraer solo el nombre (antes del " — " si existe)
                      const displayName = p.title.split(/\s*[—–]\s*/)[0].trim();
                      return (
                        <button
                          key={p.id}
                          onClick={async () => {
                            await onAssign(item.id, displayName, p.id);
                            setOpen(false);
                          }}
                          className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-[11px] ls-text2 hover:ls-bg-input transition"
                        >
                          <User className="h-3 w-3 ls-text-muted shrink-0" />
                          <span className="truncate">{p.title}</span>
                        </button>
                      );
                    })
                  )}
                </div>
                <button
                  onClick={() => {
                    openWindow("manage-patients", "Gestionar Pacientes", "manage-patients");
                    setOpen(false);
                  }}
                  className="flex w-full items-center gap-1 mt-1.5 pt-1.5 border-t ls-border text-[10px] text-cyan-400 hover:text-cyan-300 transition"
                >
                  <Plus className="h-3 w-3" />
                  Crear paciente en Gestor
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
