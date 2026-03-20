import { useState, useCallback, useEffect } from "react";
import { TabNavigation } from "./tab-navigation";
import { ModuleLoader } from "./module-loader";
import { MODULE_IDS, type ModuleId } from "@/lib/constants";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function ClinicalLayout() {
  const [activeTab, setActiveTab] = useState<ModuleId>("patient-info");

  const currentIndex = MODULE_IDS.indexOf(activeTab);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < MODULE_IDS.length - 1;

  const goPrev = useCallback(() => {
    if (hasPrev) setActiveTab(MODULE_IDS[currentIndex - 1]);
  }, [currentIndex, hasPrev]);

  const goNext = useCallback(() => {
    if (hasNext) setActiveTab(MODULE_IDS[currentIndex + 1]);
  }, [currentIndex, hasNext]);

  // Keyboard navigation: Ctrl+Left/Right
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "ArrowLeft") {
        e.preventDefault();
        goPrev();
      } else if (e.ctrlKey && e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goPrev, goNext]);

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Tab Navigation */}
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Module Content */}
      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-4xl p-6">
          <ModuleLoader moduleId={activeTab} />
        </div>
      </ScrollArea>

      {/* Bottom navigation */}
      <div className="flex items-center justify-between border-t border-white/5 bg-slate-900/50 px-4 py-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={goPrev}
          disabled={!hasPrev}
          className="gap-1 text-white/50 hover:text-white"
        >
          <ChevronLeft className="h-4 w-4" />
          Anterior
        </Button>

        <span className="text-xs text-white/30">
          {currentIndex + 1} / {MODULE_IDS.length}
        </span>

        <Button
          variant="ghost"
          size="sm"
          onClick={goNext}
          disabled={!hasNext}
          className="gap-1 text-white/50 hover:text-white"
        >
          Siguiente
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
