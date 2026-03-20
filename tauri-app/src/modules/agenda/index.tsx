import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { CalendarDays, Plus, Trash2, Clock } from "lucide-react";

interface Appointment {
  id: string;
  patientName: string;
  date: string;
  time: string;
  duration: number;
  notes: string;
}

const MOCK_APPOINTMENTS: Appointment[] = [
  {
    id: "1",
    patientName: "Maria Garcia",
    date: "2026-03-20",
    time: "09:00",
    duration: 30,
    notes: "Control audiometrico",
  },
  {
    id: "2",
    patientName: "Juan Perez",
    date: "2026-03-20",
    time: "09:45",
    duration: 45,
    notes: "Primera consulta - evaluacion completa",
  },
  {
    id: "3",
    patientName: "Ana Rodriguez",
    date: "2026-03-20",
    time: "11:00",
    duration: 30,
    notes: "Impedanciometria + reflejos",
  },
  {
    id: "4",
    patientName: "Carlos Lopez",
    date: "2026-03-21",
    time: "08:30",
    duration: 60,
    notes: "Adaptacion de audifonos",
  },
];

export default function AgendaModule() {
  const [appointments, setAppointments] = useState<Appointment[]>(MOCK_APPOINTMENTS);
  const [newAppt, setNewAppt] = useState({
    patientName: "",
    date: "",
    time: "",
    duration: 30,
    notes: "",
  });

  const addAppointment = () => {
    if (!newAppt.patientName || !newAppt.date || !newAppt.time) return;
    const appointment: Appointment = {
      id: Date.now().toString(),
      ...newAppt,
    };
    setAppointments((prev) => [...prev, appointment].sort((a, b) => {
      const dateA = `${a.date}T${a.time}`;
      const dateB = `${b.date}T${b.time}`;
      return dateA.localeCompare(dateB);
    }));
    setNewAppt({ patientName: "", date: "", time: "", duration: 30, notes: "" });
  };

  const removeAppointment = (id: string) => {
    setAppointments((prev) => prev.filter((a) => a.id !== id));
  };

  // Agrupar por fecha
  const grouped = appointments.reduce<Record<string, Appointment[]>>((acc, appt) => {
    if (!acc[appt.date]) acc[appt.date] = [];
    acc[appt.date].push(appt);
    return acc;
  }, {});

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + "T12:00:00");
    return date.toLocaleDateString("es-CL", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <CalendarDays className="h-5 w-5 text-blue-400" />
        <h2 className="text-lg font-semibold text-white">Agenda</h2>
      </div>

      {/* Agregar nueva cita */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Nueva Cita
        </legend>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1.5">
            <Label className="ls-text2">Paciente</Label>
            <Input
              value={newAppt.patientName}
              onChange={(e) => setNewAppt((p) => ({ ...p, patientName: e.target.value }))}
              className="ls-border ls-bg-input text-white"
              placeholder="Nombre del paciente"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Fecha</Label>
            <Input
              type="date"
              value={newAppt.date}
              onChange={(e) => setNewAppt((p) => ({ ...p, date: e.target.value }))}
              className="ls-border ls-bg-input text-white"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Hora</Label>
            <Input
              type="time"
              value={newAppt.time}
              onChange={(e) => setNewAppt((p) => ({ ...p, time: e.target.value }))}
              className="ls-border ls-bg-input text-white"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Duracion (min)</Label>
            <Input
              type="number"
              min={15}
              max={120}
              step={15}
              value={newAppt.duration}
              onChange={(e) => setNewAppt((p) => ({ ...p, duration: Number(e.target.value) }))}
              className="ls-border ls-bg-input text-white"
            />
          </div>
          <div className="flex items-end">
            <Button type="button" size="sm" className="gap-1.5 w-full" onClick={addAppointment}>
              <Plus className="h-3.5 w-3.5" />Agregar
            </Button>
          </div>
        </div>
        <div className="space-y-1.5">
          <Label className="ls-text2">Notas</Label>
          <Input
            value={newAppt.notes}
            onChange={(e) => setNewAppt((p) => ({ ...p, notes: e.target.value }))}
            className="ls-border ls-bg-input text-white"
            placeholder="Motivo de la cita o notas adicionales..."
          />
        </div>
      </fieldset>

      {/* Lista de citas agrupadas por fecha */}
      {Object.keys(grouped).length === 0 ? (
        <div className="rounded-lg border ls-border ls-bg-input p-8 text-center">
          <CalendarDays className="mx-auto h-10 w-10 ls-text-muted" />
          <p className="mt-2 text-sm ls-text-muted">No hay citas agendadas</p>
        </div>
      ) : (
        Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, appts]) => (
            <fieldset key={date} className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
              <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
                {formatDate(date)}
              </legend>
              <div className="space-y-2">
                {appts.map((appt) => (
                  <div
                    key={appt.id}
                    className="flex items-center justify-between rounded-md border ls-border ls-bg-input px-4 py-3"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1.5 text-blue-400">
                        <Clock className="h-4 w-4" />
                        <span className="text-sm font-medium">{appt.time}</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{appt.patientName}</p>
                        {appt.notes && (
                          <p className="text-xs ls-text-muted">{appt.notes}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs ls-text-muted">{appt.duration} min</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeAppointment(appt.id)}
                        className="h-7 w-7 p-0 ls-text-muted hover:text-red-400"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </fieldset>
          ))
      )}
    </div>
  );
}
