import { useState, useMemo } from "react";
import {
  TimpanogramChart,
  type TimpanogramData,
} from "@/charts/timpanogram/timpanogram-chart";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, RotateCcw } from "lucide-react";

const FREQUENCIES = ["500", "1000", "2000", "4000"] as const;

interface TimpValues {
  complianceMaxima: string;
  presion: string;
  volumenEac: string;
  gradiente: string;
}

interface ReflexValues {
  ipsi: Record<string, string>;
  contra: Record<string, string>;
}

const emptyTimp = (): TimpValues => ({
  complianceMaxima: "",
  presion: "",
  volumenEac: "",
  gradiente: "",
});

const emptyReflex = (): ReflexValues => ({
  ipsi: { "500": "", "1000": "", "2000": "", "4000": "" },
  contra: { "500": "", "1000": "", "2000": "", "4000": "" },
});

function classifyType(
  compliance: number | null,
  pressure: number | null,
): TimpanogramData["type"] {
  if (compliance === null || pressure === null) return "A";
  if (compliance < 0.2) return "B";
  if (pressure < -150) return "C";
  if (compliance < 0.4) return "As";
  if (compliance > 1.6) return "Ad";
  return "A";
}

function typeDescription(type: TimpanogramData["type"]): string {
  switch (type) {
    case "A":
      return "Normal";
    case "As":
      return "Rigidez (otosclerosis)";
    case "Ad":
      return "Hipercompliance (disrupcion osicular)";
    case "B":
      return "Plano (efusion / perforacion)";
    case "C":
      return "Presion negativa (disfuncion tubaria)";
  }
}

export function ImpedancePlaceholder() {
  const [activeEar, setActiveEar] = useState<"right" | "left">("right");

  const [timpOD, setTimpOD] = useState<TimpValues>(emptyTimp());
  const [timpOI, setTimpOI] = useState<TimpValues>(emptyTimp());
  const [reflexOD, setReflexOD] = useState<ReflexValues>(emptyReflex());
  const [reflexOI, setReflexOI] = useState<ReflexValues>(emptyReflex());

  const currentTimp = activeEar === "right" ? timpOD : timpOI;
  const setCurrentTimp = activeEar === "right" ? setTimpOD : setTimpOI;
  const currentReflex = activeEar === "right" ? reflexOD : reflexOI;
  const setCurrentReflex = activeEar === "right" ? setReflexOD : setReflexOI;

  const handleTimpChange = (field: keyof TimpValues, value: string) => {
    setCurrentTimp((prev) => ({ ...prev, [field]: value }));
  };

  const handleReflexChange = (
    mode: "ipsi" | "contra",
    freq: string,
    value: string,
  ) => {
    const upper = value.toUpperCase();
    if (upper === "A" || upper === "AU" || upper === "AUS") {
      setCurrentReflex((prev) => ({
        ...prev,
        [mode]: { ...prev[mode], [freq]: upper },
      }));
      return;
    }
    if (value === "" || /^-?\d*\.?\d*$/.test(value)) {
      setCurrentReflex((prev) => ({
        ...prev,
        [mode]: { ...prev[mode], [freq]: value },
      }));
    }
  };

  const handleClear = () => {
    if (activeEar === "right") {
      setTimpOD(emptyTimp());
      setReflexOD(emptyReflex());
    } else {
      setTimpOI(emptyTimp());
      setReflexOI(emptyReflex());
    }
  };

  const handleClearAll = () => {
    setTimpOD(emptyTimp());
    setTimpOI(emptyTimp());
    setReflexOD(emptyReflex());
    setReflexOI(emptyReflex());
  };

  // Build timpanogram data for chart
  const timpanogramData = useMemo(() => {
    const result: TimpanogramData[] = [];

    const buildEntry = (
      t: TimpValues,
      ear: "right" | "left",
    ): TimpanogramData | null => {
      const comp = t.complianceMaxima ? parseFloat(t.complianceMaxima) : null;
      const pres = t.presion ? parseFloat(t.presion) : null;
      const vol = t.volumenEac ? parseFloat(t.volumenEac) : null;
      if (comp === null && pres === null) return null;
      const type = classifyType(comp, pres);
      return {
        ear,
        type,
        peakPressure: pres ?? 0,
        peakCompliance: comp ?? 0.5,
        volume: vol ?? 1.0,
      };
    };

    const od = buildEntry(timpOD, "right");
    if (od) result.push(od);
    const oi = buildEntry(timpOI, "left");
    if (oi) result.push(oi);

    return result;
  }, [timpOD, timpOI]);

  const currentType = useMemo(() => {
    const comp = currentTimp.complianceMaxima
      ? parseFloat(currentTimp.complianceMaxima)
      : null;
    const pres = currentTimp.presion ? parseFloat(currentTimp.presion) : null;
    if (comp === null && pres === null) return null;
    return classifyType(comp, pres);
  }, [currentTimp]);

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header controls */}
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2">
        <Activity className="h-4 w-4 text-emerald-400" />
        <span className="text-xs font-medium text-white/60">
          Impedanciometro
        </span>

        <div className="ml-auto flex items-center gap-1">
          <Button
            size="xs"
            variant={activeEar === "right" ? "default" : "ghost"}
            onClick={() => setActiveEar("right")}
            className={
              activeEar === "right"
                ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                : "text-white/40"
            }
          >
            OD
          </Button>
          <Button
            size="xs"
            variant={activeEar === "left" ? "default" : "ghost"}
            onClick={() => setActiveEar("left")}
            className={
              activeEar === "left"
                ? "bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                : "text-white/40"
            }
          >
            OI
          </Button>

          <div className="mx-1 h-4 w-px bg-white/10" />

          <Button
            size="icon-xs"
            variant="ghost"
            onClick={handleClear}
            className="text-white/30 hover:text-white"
            title="Limpiar oido actual"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="xs"
            variant="ghost"
            onClick={handleClearAll}
            className="text-white/30 hover:text-white text-[10px]"
            title="Limpiar todo"
          >
            Limpiar todo
          </Button>
        </div>
      </div>

      {/* Main content */}
      <ScrollArea className="flex-1">
        <div className="flex gap-3 p-3">
          {/* Left column: inputs */}
          <div className="flex w-[280px] shrink-0 flex-col gap-3">
            {/* Timpanometry inputs */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-3">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                Timpanometria -{" "}
                {activeEar === "right" ? "Oido Derecho" : "Oido Izquierdo"}
              </h4>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-[10px] text-white/40">
                    Compliance max (ml)
                  </Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    placeholder="0.0"
                    value={currentTimp.complianceMaxima}
                    onChange={(e) =>
                      handleTimpChange("complianceMaxima", e.target.value)
                    }
                    className="h-7 border-white/10 bg-white/5 text-xs text-white placeholder:text-white/20"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-white/40">
                    Presion (daPa)
                  </Label>
                  <Input
                    type="number"
                    step="1"
                    min="-400"
                    max="200"
                    placeholder="0"
                    value={currentTimp.presion}
                    onChange={(e) =>
                      handleTimpChange("presion", e.target.value)
                    }
                    className="h-7 border-white/10 bg-white/5 text-xs text-white placeholder:text-white/20"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-white/40">
                    Volumen EAC (ml)
                  </Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    placeholder="0.0"
                    value={currentTimp.volumenEac}
                    onChange={(e) =>
                      handleTimpChange("volumenEac", e.target.value)
                    }
                    className="h-7 border-white/10 bg-white/5 text-xs text-white placeholder:text-white/20"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-white/40">Gradiente</Label>
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="0.0"
                    value={currentTimp.gradiente}
                    onChange={(e) =>
                      handleTimpChange("gradiente", e.target.value)
                    }
                    className="h-7 border-white/10 bg-white/5 text-xs text-white placeholder:text-white/20"
                  />
                </div>
              </div>

              {/* Type interpretation */}
              {currentType && (
                <div className="mt-2 flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`border-white/20 text-xs ${
                      currentType === "A"
                        ? "bg-green-500/10 text-green-400"
                        : currentType === "B"
                          ? "bg-red-500/10 text-red-400"
                          : currentType === "C"
                            ? "bg-yellow-500/10 text-yellow-400"
                            : "bg-orange-500/10 text-orange-400"
                    }`}
                  >
                    Tipo {currentType}
                  </Badge>
                  <span className="text-[10px] text-white/30">
                    {typeDescription(currentType)}
                  </span>
                </div>
              )}
            </div>

            {/* Acoustic reflexes table */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-3">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                Reflejos Acusticos
              </h4>

              <table className="w-full">
                <thead>
                  <tr className="text-[10px] text-white/40">
                    <th className="pb-1 text-left font-normal">Hz</th>
                    {FREQUENCIES.map((f) => (
                      <th key={f} className="pb-1 text-center font-normal">
                        {f}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(["ipsi", "contra"] as const).map((mode) => (
                    <tr key={mode}>
                      <td className="py-1 pr-2 text-[10px] font-medium uppercase text-white/50">
                        {mode === "ipsi" ? "Ipsi" : "Contra"}
                      </td>
                      {FREQUENCIES.map((freq) => (
                        <td key={freq} className="px-0.5 py-1">
                          <Input
                            value={currentReflex[mode][freq]}
                            onChange={(e) =>
                              handleReflexChange(mode, freq, e.target.value)
                            }
                            placeholder="dB"
                            className="h-6 w-full border-white/10 bg-white/5 text-center text-[10px] text-white placeholder:text-white/15"
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-1.5 text-[9px] text-white/20">
                Ingresar dB o escribir AUS (ausente)
              </p>
            </div>

            {/* Summary for both ears */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-3">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                Resumen
              </h4>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div>
                  <span className="text-red-400">OD:</span>{" "}
                  <span className="text-white/60">
                    {timpOD.complianceMaxima || timpOD.presion
                      ? `Tipo ${classifyType(
                          timpOD.complianceMaxima
                            ? parseFloat(timpOD.complianceMaxima)
                            : null,
                          timpOD.presion ? parseFloat(timpOD.presion) : null,
                        )} | ${timpOD.complianceMaxima || "—"} ml | ${timpOD.presion || "—"} daPa`
                      : "Sin datos"}
                  </span>
                </div>
                <div>
                  <span className="text-blue-400">OI:</span>{" "}
                  <span className="text-white/60">
                    {timpOI.complianceMaxima || timpOI.presion
                      ? `Tipo ${classifyType(
                          timpOI.complianceMaxima
                            ? parseFloat(timpOI.complianceMaxima)
                            : null,
                          timpOI.presion ? parseFloat(timpOI.presion) : null,
                        )} | ${timpOI.complianceMaxima || "—"} ml | ${timpOI.presion || "—"} daPa`
                      : "Sin datos"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right column: chart */}
          <div className="flex flex-1 flex-col">
            <div className="flex-1 rounded-lg border border-white/10 bg-white/5 p-2">
              <TimpanogramChart
                data={timpanogramData}
                width={480}
                height={340}
              />
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t border-white/5 px-3 py-1.5 text-[10px] text-white/30">
        <span>
          {activeEar === "right" ? "Oido Derecho" : "Oido Izquierdo"}
        </span>
        <span>
          {timpanogramData.length > 0
            ? `${timpanogramData.length} curva(s) activa(s)`
            : "Sin datos"}
        </span>
        <span>Timpanometria + Reflejos</span>
      </div>
    </div>
  );
}
