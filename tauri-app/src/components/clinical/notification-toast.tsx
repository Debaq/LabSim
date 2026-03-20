import { Toaster } from "@/components/ui/sonner";

export function NotificationToaster() {
  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        className: "text-sm",
      }}
    />
  );
}
