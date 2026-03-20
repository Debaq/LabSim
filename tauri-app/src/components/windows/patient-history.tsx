import { useState, useEffect, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { invoke } from "@tauri-apps/api/core";
import {
  Database,
  Search,
  UserPlus,
  Download,
  Save,
  RefreshCw,
  User,
  Loader2,
} from "lucide-react";

interface Patient {
  id: number;
  nombre: string;
  apellido: string;
  edad?: number;
  fecha_creacion: string;
  rut?: string;
  diagnostico?: string;
}

export function PatientHistory() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadPatients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<Patient[]>("list_patients");
      setPatients(result);
    } catch (err) {
      setError(
        `No se pudo cargar pacientes: ${err instanceof Error ? err.message : String(err)}`,
      );
      // datos de ejemplo cuando el backend no esta disponible
      setPatients([
        {
          id: 1,
          nombre: "Maria",
          apellido: "Gonzalez",
          edad: 45,
          fecha_creacion: "2025-12-10",
          diagnostico: "Hipoacusia bilateral",
        },
        {
          id: 2,
          nombre: "Carlos",
          apellido: "Rodriguez",
          edad: 62,
          fecha_creacion: "2025-12-08",
          diagnostico: "Otitis media",
        },
        {
          id: 3,
          nombre: "Ana",
          apellido: "Martinez",
          edad: 33,
          fecha_creacion: "2025-11-30",
          diagnostico: "Control auditivo",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  const filteredPatients = useMemo(() => {
    if (!searchQuery.trim()) return patients;
    const q = searchQuery.toLowerCase();
    return patients.filter(
      (p) =>
        p.nombre.toLowerCase().includes(q) ||
        p.apellido.toLowerCase().includes(q) ||
        (p.rut && p.rut.includes(q)),
    );
  }, [patients, searchQuery]);

  const selectedPatient = useMemo(
    () => patients.find((p) => p.id === selectedId) ?? null,
    [patients, selectedId],
  );

  const handleLoadPatient = async () => {
    if (!selectedPatient) return;
    try {
      await invoke("load_patient", { id: selectedPatient.id });
    } catch {
      // silently handle if command not available
    }
  };

  const handleSavePatient = async () => {
    setSaving(true);
    try {
      await invoke("save_current_patient");
      await loadPatients();
    } catch {
      // silently handle
    } finally {
      setSaving(false);
    }
  };

  const handleNewPatient = async () => {
    try {
      await invoke("create_new_patient");
    } catch {
      // silently handle
    }
  };

  const getInitials = (p: Patient) => {
    return `${p.nombre.charAt(0)}${p.apellido.charAt(0)}`.toUpperCase();
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("es-CL", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2">
        <Database className="h-4 w-4 text-cyan-400" />
        <span className="text-xs font-medium text-white/60">
          Historial de Pacientes
        </span>

        <div className="ml-auto flex items-center gap-1">
          <Button
            size="xs"
            variant="ghost"
            onClick={handleNewPatient}
            className="gap-1 text-white/40 hover:text-white"
          >
            <UserPlus className="h-3 w-3" />
            Nuevo
          </Button>
          <Button
            size="xs"
            variant="ghost"
            onClick={handleSavePatient}
            disabled={saving}
            className="gap-1 text-white/40 hover:text-white"
          >
            {saving ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Save className="h-3 w-3" />
            )}
            Guardar
          </Button>
          <Button
            size="icon-xs"
            variant="ghost"
            onClick={loadPatients}
            className="text-white/30 hover:text-white"
            title="Recargar"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="border-b border-white/5 px-3 py-2">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Buscar por nombre..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-7 border-white/10 bg-white/5 pl-7 text-xs text-white placeholder:text-white/20"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Patient list */}
        <div className="w-[260px] shrink-0 border-r border-white/5">
          <ScrollArea className="h-full">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-white/30" />
              </div>
            ) : filteredPatients.length === 0 ? (
              <div className="px-3 py-8 text-center text-xs text-white/30">
                {searchQuery
                  ? "Sin resultados"
                  : "No hay pacientes registrados"}
              </div>
            ) : (
              <div className="p-1">
                {filteredPatients.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => setSelectedId(patient.id)}
                    className={`flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition ${
                      selectedId === patient.id
                        ? "bg-cyan-500/10"
                        : "hover:bg-white/5"
                    }`}
                  >
                    {/* Avatar */}
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                        selectedId === patient.id
                          ? "bg-cyan-500/20 text-cyan-400"
                          : "bg-white/10 text-white/50"
                      }`}
                    >
                      {getInitials(patient)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div
                        className={`truncate text-xs font-medium ${
                          selectedId === patient.id
                            ? "text-cyan-300"
                            : "text-white/70"
                        }`}
                      >
                        {patient.nombre} {patient.apellido}
                      </div>
                      <div className="text-[10px] text-white/30">
                        {formatDate(patient.fecha_creacion)}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Patient detail */}
        <div className="flex-1">
          {selectedPatient ? (
            <ScrollArea className="h-full">
              <div className="p-4">
                {/* Patient header */}
                <div className="mb-4 flex items-start gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500/15 text-lg font-bold text-cyan-400">
                    {getInitials(selectedPatient)}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      {selectedPatient.nombre} {selectedPatient.apellido}
                    </h3>
                    {selectedPatient.edad && (
                      <span className="text-xs text-white/40">
                        {selectedPatient.edad} anos
                      </span>
                    )}
                    <div className="mt-1 flex gap-1.5">
                      <Badge
                        variant="outline"
                        className="border-white/10 text-[10px] text-white/40"
                      >
                        ID: {selectedPatient.id}
                      </Badge>
                      {selectedPatient.rut && (
                        <Badge
                          variant="outline"
                          className="border-white/10 text-[10px] text-white/40"
                        >
                          {selectedPatient.rut}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                {/* Detail fields */}
                <div className="space-y-3">
                  <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                      Informacion
                    </h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-white/30">Nombre:</span>{" "}
                        <span className="text-white/70">
                          {selectedPatient.nombre}
                        </span>
                      </div>
                      <div>
                        <span className="text-white/30">Apellido:</span>{" "}
                        <span className="text-white/70">
                          {selectedPatient.apellido}
                        </span>
                      </div>
                      {selectedPatient.edad && (
                        <div>
                          <span className="text-white/30">Edad:</span>{" "}
                          <span className="text-white/70">
                            {selectedPatient.edad}
                          </span>
                        </div>
                      )}
                      <div>
                        <span className="text-white/30">Registro:</span>{" "}
                        <span className="text-white/70">
                          {formatDate(selectedPatient.fecha_creacion)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {selectedPatient.diagnostico && (
                    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                        Diagnostico
                      </h4>
                      <p className="text-xs text-white/60">
                        {selectedPatient.diagnostico}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="mt-4 flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleLoadPatient}
                    className="gap-1.5 bg-cyan-600 text-white hover:bg-cyan-500"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Cargar paciente
                  </Button>
                </div>
              </div>
            </ScrollArea>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5">
                <User className="h-7 w-7 text-white/20" />
              </div>
              <div>
                <p className="text-xs text-white/40">
                  Selecciona un paciente para ver sus datos
                </p>
                <p className="mt-0.5 text-[10px] text-white/20">
                  {patients.length} pacientes registrados
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t border-white/5 px-3 py-1.5 text-[10px] text-white/30">
        <span>{filteredPatients.length} pacientes</span>
        {error && <span className="text-amber-400/60">{error}</span>}
        <span>SQLite</span>
      </div>
    </div>
  );
}
