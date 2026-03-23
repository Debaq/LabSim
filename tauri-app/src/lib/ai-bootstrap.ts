/**
 * Carga automática de modelos de IA al iniciar la aplicación.
 *
 * - Whisper (STT): descarga y carga automáticamente
 * - Piper TTS: descarga las 3 voces y las carga (male, female, karime)
 * - LLM: descarga el modelo más pequeño y lo carga
 *
 * Todo esto ocurre en segundo plano al montar el escritorio.
 * Si un modelo ya está descargado, solo se carga (rápido).
 * Si falla alguno, los demás siguen intentando.
 */

import { invoke } from "@tauri-apps/api/core";

interface TtsModelInfo {
  id: string;
  name: string;
  sizeMb: number;
  onnxPath: string;
  configPath: string;
  voiceId: string;
  role: string;
}

interface LlmModelInfo {
  id: string;
  name: string;
  sizeMb: number;
  filename: string;
}

let bootstrapDone = false;

export async function bootstrapAI(
  onLlmReady: () => void,
  onSpeechReady: () => void,
  onTtsReady: () => void,
  onLog: (msg: string) => void,
) {
  if (bootstrapDone) return;
  bootstrapDone = true;

  // Ejecutar los 3 en paralelo — cada uno es independiente
  await Promise.allSettled([
    loadWhisper(onSpeechReady, onLog),
    loadTts(onTtsReady, onLog),
    loadLlm(onLlmReady, onLog),
  ]);
}

// ─── Whisper (STT) ──────────────────────────────────────

async function loadWhisper(onReady: () => void, onLog: (msg: string) => void) {
  try {
    const loaded = await invoke<boolean>("speech_status");
    if (loaded) { onReady(); return; }

    onLog("Descargando Whisper...");
    await invoke<boolean>("speech_load_model");
    onReady();
    onLog("Whisper listo");
  } catch (err) {
    onLog(`Whisper: ${err}`);
  }
}

// ─── Piper TTS ──────────────────────────────────────────

async function loadTts(onReady: () => void, onLog: (msg: string) => void) {
  try {
    const loaded = await invoke<boolean>("tts_status");
    if (loaded) { onReady(); return; }

    const models = await invoke<TtsModelInfo[]>("tts_list_models");

    for (const model of models) {
      try {
        onLog(`Descargando ${model.name}...`);
        const configPath = await invoke<string>("tts_download_model", {
          modelIndex: models.indexOf(model),
        });
        await invoke<boolean>("tts_load_model", {
          configPath,
          voiceId: model.voiceId,
          label: model.name,
        });
        onLog(`${model.name} lista`);
      } catch (err) {
        onLog(`TTS ${model.name}: ${err}`);
      }
    }

    onReady();
  } catch (err) {
    onLog(`TTS: ${err}`);
  }
}

// ─── LLM ────────────────────────────────────────────────

async function loadLlm(onReady: () => void, onLog: (msg: string) => void) {
  try {
    const connected = await invoke<boolean>("llm_status").catch(() => false);
    if (connected) { onReady(); return; }

    const models = await invoke<LlmModelInfo[]>("llm_list_models");
    if (models.length === 0) return;

    // Elegir el más pequeño
    const smallest = models.reduce((a, b) => a.sizeMb < b.sizeMb ? a : b);

    onLog(`Descargando ${smallest.name}...`);
    const path = await invoke<string>("llm_download_model", {
      modelId: smallest.id,
      filename: smallest.filename,
    });

    onLog("Cargando LLM...");
    await invoke<boolean>("llm_load_model_async", { path });
    onReady();
    onLog("LLM listo");
  } catch (err) {
    onLog(`LLM: ${err}`);
  }
}
