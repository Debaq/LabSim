import { useEffect, useRef } from "react";
import { usePatientStore } from "@/stores/patient-store";

const AUTOSAVE_INTERVAL = 30_000; // 30 seconds

export function useAutosave() {
  const data = usePatientStore((s) => s.data);
  const lastSaved = useRef(data);

  useEffect(() => {
    const interval = setInterval(() => {
      if (data !== lastSaved.current) {
        lastSaved.current = data;
        // Zustand persist middleware handles localStorage automatically
        console.log("[autosave] datos guardados");
      }
    }, AUTOSAVE_INTERVAL);

    return () => clearInterval(interval);
  }, [data]);
}
