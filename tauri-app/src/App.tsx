import { Suspense } from "react";
import { RouterProvider, createRouter, createHashHistory } from "@tanstack/react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { routeTree } from "./routes/route-tree";

const hashHistory = createHashHistory();
const router = createRouter({ routeTree, history: hashHistory });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
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
