import { useState, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import {
  AudiogramChart,
  type AudiogramPoint,
} from "@/charts/audiogram/audiogram-chart";
import { useAudioStore } from "@/stores/audio-store";
import { ISO_FREQUENCIES, THRESHOLD_MIN, THRESHOLD_MAX, THRESHOLD_STEP } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Headphones,
  Play,
  Square,
  Plus,
  Minus,
  Volume2,
  VolumeX,
  RotateCcw,
} from "lucide-react";

type MaskingType = "none" | "white" | "pink" | "speech" | "narrowband";

export function AudiometerPlaceholder() {
  const {
    isPlaying,
    currentFrequency,
    currentLevel,
    currentChannel,
    transducer,
    setPlaying,
    setFrequency,
    setLevel,
    setChannel,
    setTransducer,
  } = useAudioStore();

  const [points, setPoints] = useState<AudiogramPoint[]>([]);
  const [pulsatile, setPulsatile] = useState(false);
  const [maskingType, setMaskingType] = useState<MaskingType>("none");
  const [maskingLevel, setMaskingLevel] = useState(40);
  const [duration, setDuration] = useState(1);

  const activeEar = currentChannel === "right" ? "right" as const : "left" as const;
  const activeType = transducer;

  const handleAddPoint = useCallback((point: AudiogramPoint) => {
    setPoints((prev) => {
      const filtered = prev.filter(
        (p) =>
          !(
            p.frequency === point.frequency &&
            p.ear === point.ear &&
            p.type === point.type
          ),
      );
      return [...filtered, point];
    });
  }, []);

  const handleRemovePoint = useCallback(
    (freq: number, ear: "right" | "left", type: "air" | "bone") => {
      setPoints((prev) =>
        prev.filter(
          (p) => !(p.frequency === freq && p.ear === ear && p.type === type),
        ),
      );
    },
    [],
  );

  const handlePresent = useCallback(async () => {
    if (isPlaying) {
      try {
        await invoke("stop_playback");
      } catch { /* ignore */ }
      setPlaying(false);
      return;
    }

    setPlaying(true);
    try {
      // Reproducir tono principal
      await invoke("play_tone", {
        params: {
          frequency: currentFrequency,
          duration: duration,
          levelDbfs: currentLevel,
          ...(pulsatile ? { pulsatileHz: 2.5, dutyCycle: 0.5 } : {}),
        },
      });

      // Reproducir enmascaramiento si corresponde
      if (maskingType !== "none") {
        await invoke("play_noise", {
          params: {
            noiseType: maskingType,
            duration: duration,
            levelDbfs: maskingLevel,
            ...(maskingType === "narrowband"
              ? { centerHz: currentFrequency, bandwidthHz: currentFrequency * 0.15 }
              : {}),
          },
        });
      }
    } catch { /* ignore */ }
    setPlaying(false);
  }, [isPlaying, currentFrequency, currentLevel, duration, pulsatile, maskingType, maskingLevel, setPlaying]);

  const handleRegister = useCallback(() => {
    const point: AudiogramPoint = {
      frequency: currentFrequency,
      threshold: currentLevel,
      type: activeType,
      ear: activeEar,
      masked: maskingType !== "none",
      noResponse: false,
    };
    handleAddPoint(point);
  }, [currentFrequency, currentLevel, activeType, activeEar, maskingType, handleAddPoint]);

  const handleNoResponse = useCallback(() => {
    const point: AudiogramPoint = {
      frequency: currentFrequency,
      threshold: currentLevel,
      type: activeType,
      ear: activeEar,
      masked: maskingType !== "none",
      noResponse: true,
    };
    handleAddPoint(point);
  }, [currentFrequency, currentLevel, activeType, activeEar, maskingType, handleAddPoint]);

  const adjustLevel = useCallback(
    (delta: number) => {
      const next = Math.max(THRESHOLD_MIN, Math.min(THRESHOLD_MAX, currentLevel + delta));
      setLevel(next);
    },
    [currentLevel, setLevel],
  );

  const formatFreq = (f: number) => (f >= 1000 ? `${f / 1000}k` : `${f}`);

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/10 px-3 py-2">
        <Headphones className="h-4 w-4 text-blue-400" />
        <span className="text-xs font-medium text-white/60">Audiómetro</span>

        <div className="ml-auto flex items-center gap-1">
          {/* Ear toggle */}
          <Button
            size="xs"
            variant={activeEar === "right" ? "default" : "ghost"}
            onClick={() => setChannel("right")}
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
            onClick={() => setChannel("left")}
            className={
              activeEar === "left"
                ? "bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                : "text-white/40"
            }
          >
            OI
          </Button>

          <div className="mx-1 h-4 w-px bg-white/10" />

          {/* Type toggle */}
          <Button
            size="xs"
            variant={activeType === "air" ? "default" : "ghost"}
            onClick={() => setTransducer("air")}
            className={
              activeType === "air"
                ? "bg-white/10 text-white"
                : "text-white/40"
            }
          >
            VA
          </Button>
          <Button
            size="xs"
            variant={activeType === "bone" ? "default" : "ghost"}
            onClick={() => setTransducer("bone")}
            className={
              activeType === "bone"
                ? "bg-white/10 text-white"
                : "text-white/40"
            }
          >
            VO
          </Button>

          <div className="mx-1 h-4 w-px bg-white/10" />

          <Button
            size="icon-xs"
            variant="ghost"
            onClick={() => setPoints([])}
            className="text-white/30 hover:text-white"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Chart */}
      <div className="min-h-0 flex-1 p-2">
        <AudiogramChart
          points={points}
          onPointAdd={handleAddPoint}
          onPointRemove={handleRemovePoint}
          activeEar={activeEar}
          activeType={activeType}
          interactive
        />
      </div>

      {/* Controls panel */}
      <div className="shrink-0 space-y-3 border-t border-white/10 px-3 py-3">
        {/* Frequency selector */}
        <div className="space-y-1.5">
          <Label className="text-[10px] uppercase tracking-wider text-white/40">Frecuencia (Hz)</Label>
          <div className="flex flex-wrap gap-1">
            {ISO_FREQUENCIES.map((f) => (
              <Button
                key={f}
                size="xs"
                variant={currentFrequency === f ? "default" : "ghost"}
                onClick={() => setFrequency(f)}
                className={
                  currentFrequency === f
                    ? "bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 min-w-[38px]"
                    : "text-white/50 hover:text-white min-w-[38px] border border-white/5"
                }
              >
                {formatFreq(f)}
              </Button>
            ))}
          </div>
        </div>

        {/* Intensity control + present button row */}
        <div className="flex items-stretch gap-3">
          {/* Intensity control */}
          <div className="flex flex-1 items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
            <Volume2 className="h-4 w-4 shrink-0 text-white/40" />
            <Button
              size="icon-xs"
              variant="ghost"
              onClick={() => adjustLevel(-THRESHOLD_STEP)}
              disabled={currentLevel <= THRESHOLD_MIN}
              className="text-white/60 hover:text-white"
            >
              <Minus className="h-3.5 w-3.5" />
            </Button>

            <div className="flex min-w-[60px] flex-col items-center">
              <span className="text-2xl font-bold tabular-nums text-white">{currentLevel}</span>
              <span className="text-[9px] uppercase tracking-wider text-white/30">dB HL</span>
            </div>

            <Button
              size="icon-xs"
              variant="ghost"
              onClick={() => adjustLevel(THRESHOLD_STEP)}
              disabled={currentLevel >= THRESHOLD_MAX}
              className="text-white/60 hover:text-white"
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>

            {/* Slider */}
            <input
              type="range"
              min={THRESHOLD_MIN}
              max={THRESHOLD_MAX}
              step={THRESHOLD_STEP}
              value={currentLevel}
              onChange={(e) => setLevel(Number(e.target.value))}
              className="mx-1 h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-white/10 accent-amber-500 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-amber-400"
            />
          </div>

          {/* Present button */}
          <Button
            size="lg"
            onClick={handlePresent}
            className={
              isPlaying
                ? "h-auto min-w-[100px] bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
                : "h-auto min-w-[100px] bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30"
            }
          >
            {isPlaying ? (
              <>
                <Square className="mr-1.5 h-4 w-4" />
                DETENER
              </>
            ) : (
              <>
                <Play className="mr-1.5 h-4 w-4" />
                PRESENTAR
              </>
            )}
          </Button>
        </div>

        {/* Options row */}
        <div className="flex flex-wrap items-end gap-3">
          {/* Pulsatile */}
          <div className="flex items-center gap-1.5">
            <Checkbox
              checked={pulsatile}
              onCheckedChange={(v) => setPulsatile(v === true)}
              className="border-white/20"
            />
            <Label className="text-xs text-white/60 cursor-pointer" onClick={() => setPulsatile(!pulsatile)}>
              Pulsátil
            </Label>
          </div>

          <div className="h-5 w-px bg-white/10" />

          {/* Duration */}
          <div className="space-y-1">
            <Label className="text-[10px] uppercase tracking-wider text-white/40">Duración</Label>
            <div className="flex gap-0.5">
              {[1, 2, 3].map((d) => (
                <Button
                  key={d}
                  size="xs"
                  variant={duration === d ? "default" : "ghost"}
                  onClick={() => setDuration(d)}
                  className={
                    duration === d
                      ? "bg-white/10 text-white min-w-[32px]"
                      : "text-white/40 min-w-[32px] border border-white/5"
                  }
                >
                  {d}s
                </Button>
              ))}
            </div>
          </div>

          <div className="h-5 w-px bg-white/10" />

          {/* Masking type */}
          <div className="space-y-1">
            <Label className="text-[10px] uppercase tracking-wider text-white/40">Enmascaramiento</Label>
            <Select value={maskingType} onValueChange={(v) => setMaskingType(v as MaskingType)}>
              <SelectTrigger className="h-6 min-w-[100px] border-white/10 bg-white/5 text-xs text-white" size="sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Ninguno</SelectItem>
                <SelectItem value="white">Blanco</SelectItem>
                <SelectItem value="pink">Rosa</SelectItem>
                <SelectItem value="narrowband">NBN</SelectItem>
                <SelectItem value="speech">Speech</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Masking level */}
          {maskingType !== "none" && (
            <div className="space-y-1">
              <Label className="text-[10px] uppercase tracking-wider text-white/40">Nivel mask</Label>
              <div className="flex items-center gap-1">
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => setMaskingLevel(Math.max(THRESHOLD_MIN, maskingLevel - THRESHOLD_STEP))}
                  className="text-white/50"
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <span className="min-w-[36px] text-center text-xs font-mono font-semibold text-white">
                  {maskingLevel}
                </span>
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => setMaskingLevel(Math.min(THRESHOLD_MAX, maskingLevel + THRESHOLD_STEP))}
                  className="text-white/50"
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}

          <div className="flex-1" />

          {/* Register / No Response */}
          <div className="flex gap-1.5">
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRegister}
              className="border border-white/10 bg-white/5 text-white/80 hover:bg-white/10 hover:text-white"
            >
              <Plus className="mr-1 h-3.5 w-3.5" />
              Registrar
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleNoResponse}
              className="border border-white/10 bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
            >
              <VolumeX className="mr-1 h-3.5 w-3.5" />
              Sin Respuesta
            </Button>
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-3 border-t border-white/10 px-3 py-1.5 text-[10px] text-white/30">
        <Badge variant="outline" className="h-4 border-white/10 px-1.5 text-[10px] text-white/50">
          {formatFreq(currentFrequency)} Hz
        </Badge>
        <Badge variant="outline" className="h-4 border-white/10 px-1.5 text-[10px] text-white/50">
          {currentLevel} dB
        </Badge>
        <Badge
          variant="outline"
          className={`h-4 border-white/10 px-1.5 text-[10px] ${activeEar === "right" ? "text-red-400" : "text-blue-400"}`}
        >
          {activeEar === "right" ? "OD" : "OI"}
        </Badge>
        <Badge variant="outline" className="h-4 border-white/10 px-1.5 text-[10px] text-white/50">
          {activeType === "air" ? "Vía Aérea" : "Vía Ósea"}
        </Badge>
        {maskingType !== "none" && (
          <Badge variant="outline" className="h-4 border-white/10 px-1.5 text-[10px] text-yellow-400">
            Mask: {maskingType} {maskingLevel} dB
          </Badge>
        )}
        {pulsatile && (
          <Badge variant="outline" className="h-4 border-white/10 px-1.5 text-[10px] text-purple-400">
            Pulsátil
          </Badge>
        )}
        <span className="ml-auto">
          {isPlaying ? "Reproduciendo..." : `${points.length} puntos`}
        </span>
      </div>
    </div>
  );
}
