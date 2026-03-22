import { useState, useEffect, useCallback, useMemo } from "react";
import {
  useLarissaStore,
  type AgendaItem,
  type Evolution,
  type Interconsultation,
} from "@/stores/larissa-store";
import { useAuthStore } from "@/stores/auth-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAgendaTimerStore } from "@/stores/agenda-timer-store";
import { toast } from "sonner";
import {
  ClipboardPen,
  CalendarDays,
  Clock,
  User,
  Loader2,
  Plus,
  FileText,
  ArrowRightLeft,
  FlaskConical,
  FolderOpen,
  Send,
  AlertCircle,
  Play,
  Square,
  Phone,
} from "lucide-react";

// ─── Helpers ─────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  rescheduled: "Reagendada",
  no_show: "No asistió",
};

const STATUS_COLORS: Record<string, string> = {
  scheduled: "text-sky-400 bg-sky-500/10",
  in_progress: "text-amber-400 bg-amber-500/10",
  completed: "text-emerald-400 bg-emerald-500/10",
  cancelled: "text-zinc-400 bg-zinc-500/10",
  rescheduled: "text-orange-400 bg-orange-500/10",
  no_show: "text-red-400 bg-red-500/10",
};

const IC_STATUS_LABELS: Record<string, string> = {
  solicitada: "Solicitada",
  respondida: "Respondida",
  completada: "Completada",
};

const IC_STATUS_COLORS: Record<string, string> = {
  solicitada: "text-amber-400 bg-amber-500/10",
  respondida: "text-sky-400 bg-sky-500/10",
  completada: "text-emerald-400 bg-emerald-500/10",
};

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (d.getTime() === today.getTime()) return "Hoy";
    if (d.getTime() === tomorrow.getTime()) return "Mañana";
    return d.toLocaleDateString("es-CL", { weekday: "short", day: "2-digit", month: "short" });
  } catch {
    return dateStr;
  }
}

function formatTime(time: string) {
  return time?.slice(0, 5) ?? "";
}

function formatDateTime(dt: string) {
  try {
    return new Date(dt).toLocaleString("es-CL", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dt;
  }
}

// ─── Main Component ──────────────────────────────────

export function LarissaWindow() {
  const {
    agendaItems,
    agendaLoading,
    selectedItemId,
    selectedCase,
    caseLoading,
    evolutions,
    interconsultations,
    detailLoading,
    activeTab,
    setActiveTab,
    fetchAgenda,
    selectItem,
    createEvolution,
    createInterconsultation,
  } = useLarissaStore();

  const role = useAuthStore((s) => s.role);

  // Live session
  const activePatientId = useLiveSessionStore((s) => s.activePatientId);
  const startAttention = useLiveSessionStore((s) => s.startAttention);
  const endAttention = useLiveSessionStore((s) => s.endAttention);
  const setPatientContact = useChatStore((s) => s.setPatientContact);
  const removePatientContact = useChatStore((s) => s.removePatientContact);
  const startKarimeTimer = useAgendaTimerStore((s) => s.startAppointment);
  const endKarimeTimer = useAgendaTimerStore((s) => s.endAppointment);

  const [evoDialogOpen, setEvoDialogOpen] = useState(false);
  const [icDialogOpen, setIcDialogOpen] = useState(false);

  const isAttending = activePatientId !== null;

  useEffect(() => {
    fetchAgenda();
  }, [fetchAgenda]);

  const selectedAgendaItem = useMemo(
    () => agendaItems.find((a) => a.id === selectedItemId) ?? null,
    [agendaItems, selectedItemId],
  );

  // Agrupar citas por fecha
  const groupedItems = useMemo(() => {
    const groups: Record<string, AgendaItem[]> = {};
    for (const item of agendaItems) {
      const key = item.scheduled_date;
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [agendaItems]);

  // Info del paciente desde el caso
  const patientInfo = selectedCase?.patientInfo as Record<string, string> | undefined;

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <ClipboardPen className="h-4 w-4 text-cyan-400" />
        <span className="text-xs font-medium ls-text2">Larissa</span>
        {selectedAgendaItem && (
          <span className="text-xs ls-text-muted">— {selectedAgendaItem.patient_name}</span>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── Agenda (izquierda) ─── */}
        <div className="w-[280px] shrink-0 border-r ls-border">
          <div className="border-b ls-border px-3 py-2">
            <div className="flex items-center gap-1.5">
              <CalendarDays className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-[10px] font-bold uppercase tracking-wider ls-text-muted">
                Agenda de Atenciones
              </span>
            </div>
          </div>

          <ScrollArea className="h-full">
            {agendaLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
              </div>
            ) : groupedItems.length === 0 ? (
              <div className="px-3 py-8 text-center text-xs ls-text-muted">
                No hay citas programadas
              </div>
            ) : (
              <div className="p-1">
                {groupedItems.map(([date, items]) => (
                  <div key={date} className="mb-2">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider ls-text-muted">
                      {formatDate(date)}
                    </div>
                    {items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => selectItem(item.id)}
                        className={`flex w-full flex-col gap-0.5 rounded-md px-2.5 py-2 text-left transition ${
                          selectedItemId === item.id ? "bg-cyan-500/10" : "hover:ls-bg-input"
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 ls-text-muted" />
                          <span className="text-[11px] font-medium ls-text2">
                            {formatTime(item.scheduled_time)}
                          </span>
                          <span className="text-[11px] ls-text-muted">
                            ({item.duration_minutes} min)
                          </span>
                        </div>
                        <span
                          className={`truncate text-xs font-medium ${
                            selectedItemId === item.id ? "text-cyan-300" : "ls-text2"
                          }`}
                        >
                          {item.patient_name}
                        </span>
                        <div className="flex items-center gap-1">
                          {item.procedure_name && (
                            <span className="truncate text-[10px] ls-text-muted">
                              {item.procedure_name}
                            </span>
                          )}
                          <Badge
                            variant="outline"
                            className={`ml-auto px-1 py-0 text-[8px] ${STATUS_COLORS[item.status] ?? ""}`}
                          >
                            {STATUS_LABELS[item.status] ?? item.status}
                          </Badge>
                        </div>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* ─── Ficha Clínica (derecha) ─── */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {selectedAgendaItem ? (
            <>
              {/* Patient header */}
              <div className="border-b ls-border px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold ${
                    isAttending && activePatientId === selectedAgendaItem.id
                      ? "bg-emerald-500/20 text-emerald-400 ring-2 ring-emerald-500/30"
                      : "bg-cyan-500/15 text-cyan-400"
                  }`}>
                    {selectedAgendaItem.patient_name
                      .split(" ")
                      .map((w) => w[0])
                      .slice(0, 2)
                      .join("")
                      .toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold ls-text">
                      {selectedAgendaItem.patient_name}
                    </h3>
                    <div className="flex items-center gap-2 text-xs ls-text-muted">
                      {patientInfo?.gender && <span>{patientInfo.gender}</span>}
                      {selectedAgendaItem.patient_age && (
                        <span>{selectedAgendaItem.patient_age} años</span>
                      )}
                      {patientInfo?.healthInsurance && <span>{patientInfo.healthInsurance}</span>}
                      {selectedAgendaItem.procedure_name && (
                        <Badge variant="outline" className="text-[10px] ls-border ls-text-muted">
                          {selectedAgendaItem.procedure_name}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {/* Botones de atención */}
                  {isAttending && activePatientId === selectedAgendaItem.id ? (
                    <Button
                      size="xs"
                      variant="outline"
                      onClick={async () => {
                        endKarimeTimer();
                        await endAttention();
                        removePatientContact();
                        toast.success("Atención finalizada");
                      }}
                      className="gap-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
                    >
                      <Square className="h-3 w-3" />
                      Finalizar
                    </Button>
                  ) : !isAttending ? (
                    <Button
                      size="xs"
                      onClick={() => {
                        const personality = selectedCase?.personality as Record<string, string> | undefined;
                        const displayName = personality?.displayName || selectedAgendaItem.patient_name;
                        // Iniciar live session
                        startAttention({
                          patientId: selectedAgendaItem.id,
                          caseId: selectedAgendaItem.case_id ?? selectedAgendaItem.id,
                          agendaItemId: selectedAgendaItem.id,
                          displayName,
                        });
                        // Paciente aparece en chat
                        setPatientContact(displayName);
                        // Karime inicia timer de presión
                        startKarimeTimer({
                          id: selectedAgendaItem.id,
                          patientName: displayName,
                          procedureName: selectedAgendaItem.procedure_name ?? undefined,
                          scheduledTime: selectedAgendaItem.scheduled_time,
                          durationMinutes: selectedAgendaItem.duration_minutes ?? 30,
                          startedAt: null,
                        });
                        toast.success(`Atendiendo a ${displayName}`);
                      }}
                      className="gap-1 bg-emerald-600 text-white hover:bg-emerald-500"
                    >
                      <Phone className="h-3 w-3" />
                      Llamar Paciente
                    </Button>
                  ) : null}
                </div>
              </div>

              {/* Tabs */}
              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as typeof activeTab)}
                className="flex flex-1 flex-col overflow-hidden"
              >
                <TabsList variant="line" className="px-4">
                  <TabsTrigger value="evoluciones" className="gap-1 text-xs">
                    <FileText className="h-3 w-3" />
                    Evoluciones
                    {evolutions.length > 0 && (
                      <Badge variant="secondary" className="ml-1 h-4 px-1 text-[9px]">
                        {evolutions.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="interconsultas" className="gap-1 text-xs">
                    <ArrowRightLeft className="h-3 w-3" />
                    Interconsultas
                    {interconsultations.length > 0 && (
                      <Badge variant="secondary" className="ml-1 h-4 px-1 text-[9px]">
                        {interconsultations.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="examenes" className="gap-1 text-xs">
                    <FlaskConical className="h-3 w-3" />
                    Exámenes
                  </TabsTrigger>
                  <TabsTrigger value="ficha-base" className="gap-1 text-xs">
                    <FolderOpen className="h-3 w-3" />
                    Ficha Base
                  </TabsTrigger>
                </TabsList>

                {detailLoading || caseLoading ? (
                  <div className="flex flex-1 items-center justify-center">
                    <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
                  </div>
                ) : (
                  <>
                    <TabsContent value="evoluciones" className="flex-1 overflow-hidden">
                      <EvolucionesTab
                        evolutions={evolutions}
                        onNew={() => setEvoDialogOpen(true)}
                      />
                    </TabsContent>
                    <TabsContent value="interconsultas" className="flex-1 overflow-hidden">
                      <InterconsultasTab
                        interconsultations={interconsultations}
                        onNew={() => setIcDialogOpen(true)}
                        role={role}
                      />
                    </TabsContent>
                    <TabsContent value="examenes" className="flex-1 overflow-hidden">
                      <ExamenesTab caseProfile={selectedCase} />
                    </TabsContent>
                    <TabsContent value="ficha-base" className="flex-1 overflow-hidden">
                      <FichaBaseTab caseProfile={selectedCase} />
                    </TabsContent>
                  </>
                )}
              </Tabs>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl ls-bg-input">
                <User className="h-7 w-7 ls-text-muted" />
              </div>
              <div>
                <p className="text-xs ls-text-muted">Selecciona una atención de la agenda</p>
                <p className="mt-0.5 text-xs ls-text-muted">
                  {agendaItems.length} citas programadas
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
        <span>{agendaItems.length} atenciones</span>
        {selectedAgendaItem && (
          <span>
            {evolutions.length} evoluciones · {interconsultations.length} interconsultas
          </span>
        )}
      </div>

      {/* Diálogo Nueva Evolución */}
      <NewEvolutionDialog
        open={evoDialogOpen}
        onOpenChange={setEvoDialogOpen}
        onSubmit={createEvolution}
      />

      {/* Diálogo Nueva Interconsulta */}
      <NewInterconsultationDialog
        open={icDialogOpen}
        onOpenChange={setIcDialogOpen}
        onSubmit={createInterconsultation}
      />
    </div>
  );
}

// ─── Tab: Evoluciones ────────────────────────────────

function EvolucionesTab({
  evolutions,
  onNew,
}: {
  evolutions: Evolution[];
  onNew: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b ls-border px-4 py-2">
        <span className="text-xs ls-text-muted">Evoluciones clínicas</span>
        <Button size="xs" onClick={onNew} className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500">
          <Plus className="h-3 w-3" />
          Nueva Evolución
        </Button>
      </div>
      <ScrollArea className="flex-1">
        {evolutions.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs ls-text-muted">
            No hay evoluciones registradas
          </div>
        ) : (
          <div className="space-y-3 p-4">
            {evolutions.map((evo) => (
              <div key={evo.id} className="rounded-lg border ls-border ls-bg-input p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-medium ls-text2">
                    {evo.student_name ?? evo.student_username}
                  </span>
                  <span className="text-[10px] ls-text-muted">{formatDateTime(evo.created_at)}</span>
                </div>
                <div className="space-y-2 text-xs">
                  {evo.motivo_consulta && (
                    <EvolutionField label="Motivo de consulta" value={evo.motivo_consulta} />
                  )}
                  {evo.anamnesis_proxima && (
                    <EvolutionField label="Anamnesis próxima" value={evo.anamnesis_proxima} />
                  )}
                  {evo.examen_fisico && (
                    <EvolutionField label="Examen físico" value={evo.examen_fisico} />
                  )}
                  {evo.hipotesis_diagnostica && (
                    <EvolutionField label="Hipótesis diagnóstica" value={evo.hipotesis_diagnostica} />
                  )}
                  {evo.plan_estudio && (
                    <EvolutionField label="Plan de estudio" value={evo.plan_estudio} />
                  )}
                  {evo.plan_terapeutico && (
                    <EvolutionField label="Plan terapéutico" value={evo.plan_terapeutico} />
                  )}
                  {evo.observaciones && (
                    <EvolutionField label="Observaciones" value={evo.observaciones} />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

function EvolutionField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="font-medium text-cyan-400/80">{label}:</span>{" "}
      <span className="ls-text2 whitespace-pre-wrap">{value}</span>
    </div>
  );
}

// ─── Tab: Interconsultas ─────────────────────────────

function InterconsultasTab({
  interconsultations,
  onNew,
  role,
}: {
  interconsultations: Interconsultation[];
  onNew: () => void;
  role: string;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b ls-border px-4 py-2">
        <span className="text-xs ls-text-muted">Interconsultas</span>
        <Button size="xs" onClick={onNew} className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500">
          <Plus className="h-3 w-3" />
          Solicitar Interconsulta
        </Button>
      </div>
      <ScrollArea className="flex-1">
        {interconsultations.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs ls-text-muted">
            No hay interconsultas
          </div>
        ) : (
          <div className="space-y-3 p-4">
            {interconsultations.map((ic) => (
              <div key={ic.id} className="rounded-lg border ls-border ls-bg-input p-3">
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium ls-text2">{ic.target_specialty}</span>
                    <Badge
                      variant="outline"
                      className={`px-1 py-0 text-[9px] ${IC_STATUS_COLORS[ic.status] ?? ""}`}
                    >
                      {IC_STATUS_LABELS[ic.status] ?? ic.status}
                    </Badge>
                    {ic.priority === "urgente" && (
                      <Badge variant="outline" className="px-1 py-0 text-[9px] text-red-400 bg-red-500/10">
                        Urgente
                      </Badge>
                    )}
                  </div>
                  <span className="text-[10px] ls-text-muted">{formatDateTime(ic.created_at)}</span>
                </div>
                <div className="text-xs">
                  <div className="mb-1">
                    <span className="ls-text-muted">Solicitante:</span>{" "}
                    <span className="ls-text2">{ic.requester_name ?? ic.requester_username}</span>
                  </div>
                  <div className="mb-1">
                    <span className="ls-text-muted">Motivo:</span>{" "}
                    <span className="ls-text2">{ic.reason}</span>
                  </div>
                  {ic.response_text && (
                    <div className="mt-2 rounded border ls-border p-2">
                      <span className="text-[10px] font-medium text-emerald-400">Respuesta:</span>
                      <p className="mt-0.5 ls-text2 whitespace-pre-wrap">{ic.response_text}</p>
                      {ic.responder_name && (
                        <span className="text-[10px] ls-text-muted">— {ic.responder_name}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

// ─── Tab: Exámenes ───────────────────────────────────

function ExamenesTab({ caseProfile }: { caseProfile: Record<string, unknown> | null }) {
  if (!caseProfile) {
    return (
      <div className="flex h-full items-center justify-center text-xs ls-text-muted">
        No hay caso vinculado a esta cita
      </div>
    );
  }

  const examModules = [
    { key: "audiometry", label: "Audiometría" },
    { key: "logoaudiometry", label: "Logoaudiometría" },
    { key: "supraliminal", label: "Supraliminal" },
    { key: "impedance", label: "Impedanciometría" },
    { key: "oae", label: "Emisiones Otoacústicas" },
    { key: "abr", label: "Potenciales Evocados" },
    { key: "electrocochleo", label: "Electrococleografía" },
    { key: "hearingAids", label: "Audífonos" },
    { key: "oct", label: "OCT" },
    { key: "visualField", label: "Campo Visual" },
    { key: "retinography", label: "Retinografía" },
    { key: "cornealTopography", label: "Topografía Corneal" },
  ];

  const available = examModules.filter((m) => {
    const data = caseProfile[m.key];
    return data && typeof data === "object" && Object.keys(data as object).length > 0;
  });

  return (
    <ScrollArea className="h-full">
      <div className="p-4">
        {available.length === 0 ? (
          <div className="py-8 text-center text-xs ls-text-muted">
            No hay resultados de exámenes vinculados
          </div>
        ) : (
          <div className="space-y-3">
            {available.map((m) => {
              const data = caseProfile[m.key] as Record<string, unknown>;
              const fieldCount = Object.keys(data).length;
              return (
                <div key={m.key} className="rounded-lg border ls-border ls-bg-input p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium ls-text2">{m.label}</span>
                    <Badge variant="outline" className="text-[9px] ls-border ls-text-muted">
                      {fieldCount} campos
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

// ─── Tab: Ficha Base ─────────────────────────────────

function FichaBaseTab({ caseProfile }: { caseProfile: Record<string, unknown> | null }) {
  if (!caseProfile) {
    return (
      <div className="flex h-full items-center justify-center text-xs ls-text-muted">
        No hay caso vinculado a esta cita
      </div>
    );
  }

  const patientInfo = (caseProfile.patientInfo ?? {}) as Record<string, unknown>;
  const anamnesis = (caseProfile.anamnesis ?? {}) as Record<string, unknown>;

  const FIELD_LABELS: Record<string, string> = {
    firstName: "Nombre",
    lastName: "Apellido",
    documentId: "RUN/Documento",
    birthDate: "Fecha de nacimiento",
    age: "Edad",
    gender: "Sexo",
    phone: "Teléfono",
    email: "Correo",
    address: "Dirección",
    city: "Ciudad",
    occupation: "Ocupación",
    referredBy: "Derivado por",
    healthInsurance: "Previsión",
    notes: "Observaciones",
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4 p-4">
        {/* Identificación */}
        <fieldset className="rounded-lg border ls-border ls-bg-input p-3">
          <legend className="px-2 text-[10px] font-bold uppercase tracking-wider ls-text-muted">
            Identificación del Paciente
          </legend>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(patientInfo).map(([key, val]) =>
              val ? (
                <div key={key}>
                  <span className="ls-text-muted">{FIELD_LABELS[key] ?? key}:</span>{" "}
                  <span className="ls-text2">{String(val)}</span>
                </div>
              ) : null,
            )}
          </div>
          {Object.keys(patientInfo).length === 0 && (
            <p className="text-xs ls-text-muted">Sin datos de identificación</p>
          )}
        </fieldset>

        {/* Anamnesis */}
        <fieldset className="rounded-lg border ls-border ls-bg-input p-3">
          <legend className="px-2 text-[10px] font-bold uppercase tracking-wider ls-text-muted">
            Anamnesis Remota
          </legend>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(anamnesis).map(([key, val]) =>
              val ? (
                <div key={key} className="col-span-2">
                  <span className="ls-text-muted">{key}:</span>{" "}
                  <span className="ls-text2 whitespace-pre-wrap">{String(val)}</span>
                </div>
              ) : null,
            )}
          </div>
          {Object.keys(anamnesis).length === 0 && (
            <p className="text-xs ls-text-muted">Sin datos de anamnesis</p>
          )}
        </fieldset>
      </div>
    </ScrollArea>
  );
}

// ─── Diálogo: Nueva Evolución ────────────────────────

function NewEvolutionDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: Record<string, string>) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    motivoConsulta: "",
    anamnesisProxima: "",
    examenFisico: "",
    hipotesisDiagnostica: "",
    planEstudio: "",
    planTerapeutico: "",
    observaciones: "",
  });

  const updateField = (key: string, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async () => {
    if (!form.motivoConsulta.trim()) {
      toast.error("El motivo de consulta es obligatorio");
      return;
    }
    setSaving(true);
    try {
      await onSubmit(form);
      toast.success("Evolución registrada");
      setForm({
        motivoConsulta: "",
        anamnesisProxima: "",
        examenFisico: "",
        hipotesisDiagnostica: "",
        planEstudio: "",
        planTerapeutico: "",
        observaciones: "",
      });
      onOpenChange(false);
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-h-[80vh] max-w-lg overflow-hidden">
        <DialogHeader>
          <DialogTitle className="ls-text">Nueva Evolución Clínica</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh] pr-2">
          <div className="space-y-3 p-1">
            <EvoField
              label="Motivo de consulta *"
              value={form.motivoConsulta}
              onChange={(v) => updateField("motivoConsulta", v)}
            />
            <EvoField
              label="Anamnesis próxima"
              value={form.anamnesisProxima}
              onChange={(v) => updateField("anamnesisProxima", v)}
              rows={3}
            />
            <EvoField
              label="Examen físico"
              value={form.examenFisico}
              onChange={(v) => updateField("examenFisico", v)}
              rows={3}
            />
            <EvoField
              label="Hipótesis diagnóstica"
              value={form.hipotesisDiagnostica}
              onChange={(v) => updateField("hipotesisDiagnostica", v)}
            />
            <EvoField
              label="Plan de estudio"
              value={form.planEstudio}
              onChange={(v) => updateField("planEstudio", v)}
            />
            <EvoField
              label="Plan terapéutico / Indicaciones"
              value={form.planTerapeutico}
              onChange={(v) => updateField("planTerapeutico", v)}
              rows={3}
            />
            <EvoField
              label="Observaciones"
              value={form.observaciones}
              onChange={(v) => updateField("observaciones", v)}
            />
          </div>
        </ScrollArea>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="ls-border ls-text2">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={saving}
            className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500"
          >
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
            Registrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EvoField({
  label,
  value,
  onChange,
  rows = 2,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-xs ls-text2">{label}</Label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="ls-border ls-bg-input text-xs ls-text placeholder:ls-text-muted resize-none"
      />
    </div>
  );
}

// ─── Diálogo: Nueva Interconsulta ────────────────────

const SPECIALTIES = [
  "Audiología",
  "Otoneurología",
  "Oftalmología",
  "Otorrinolaringología",
  "Neurología",
  "Medicina General",
  "Fonoaudiología",
  "Otra",
];

function NewInterconsultationDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: { targetSpecialty: string; reason: string; priority?: string }) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [specialty, setSpecialty] = useState("");
  const [reason, setReason] = useState("");
  const [priority, setPriority] = useState<"normal" | "urgente">("normal");

  const handleSubmit = async () => {
    if (!specialty.trim() || !reason.trim()) {
      toast.error("Especialidad y motivo son obligatorios");
      return;
    }
    setSaving(true);
    try {
      await onSubmit({ targetSpecialty: specialty, reason, priority });
      toast.success("Interconsulta solicitada");
      setSpecialty("");
      setReason("");
      setPriority("normal");
      onOpenChange(false);
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-w-md">
        <DialogHeader>
          <DialogTitle className="ls-text">Solicitar Interconsulta</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Especialidad destino *</Label>
            <div className="flex flex-wrap gap-1">
              {SPECIALTIES.map((s) => (
                <button
                  key={s}
                  onClick={() => setSpecialty(s)}
                  className={`rounded-md px-2 py-1 text-[11px] transition ${
                    specialty === s
                      ? "bg-cyan-500/15 text-cyan-400"
                      : "ls-bg-input ls-text-muted hover:ls-text2"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Motivo *</Label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Describa el motivo de la interconsulta..."
              className="ls-border ls-bg-input text-xs ls-text placeholder:ls-text-muted resize-none"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Prioridad</Label>
            <div className="flex gap-2">
              <button
                onClick={() => setPriority("normal")}
                className={`rounded-md px-3 py-1 text-xs transition ${
                  priority === "normal"
                    ? "bg-sky-500/15 text-sky-400"
                    : "ls-bg-input ls-text-muted"
                }`}
              >
                Normal
              </button>
              <button
                onClick={() => setPriority("urgente")}
                className={`rounded-md px-3 py-1 text-xs transition ${
                  priority === "urgente"
                    ? "bg-red-500/15 text-red-400"
                    : "ls-bg-input ls-text-muted"
                }`}
              >
                Urgente
              </button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="ls-border ls-text2">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={saving}
            className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500"
          >
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
            Solicitar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
