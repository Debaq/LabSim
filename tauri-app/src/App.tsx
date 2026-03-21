import { Suspense, useEffect } from "react";
import { RouterProvider, createRouter, createHashHistory } from "@tanstack/react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { routeTree } from "./routes/route-tree";
import { getCurrentWindow } from "@tauri-apps/api/window";

const hashHistory = createHashHistory();
const router = createRouter({ routeTree, history: hashHistory });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  // F11 toggle fullscreen
  useEffect(() => {
    const handler = async (e: KeyboardEvent) => {
      if (e.key === "F11") {
        e.preventDefault();
        const win = getCurrentWindow();
        const fs = await win.isFullscreen();
        await win.setFullscreen(!fs);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <TooltipProvider>
      <Suspense
        fallback={
          <div className="flex h-screen items-center justify-center bg-slate-900">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-white">LabSim</h1>
              <p className="mt-2 text-sm text-white/50">Cargando...</p>
            </div>
          </div>
        }
      >
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors closeButton />
      </Suspense>
    </TooltipProvider>
  );
}

export default App;
