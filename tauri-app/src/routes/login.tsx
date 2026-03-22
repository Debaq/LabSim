import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/stores/auth-store";
import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import { Loader2, Cross, KeyRound } from "lucide-react";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const mustChangePassword = useAuthStore((s) => s.mustChangePassword);
  const clearMustChangePassword = useAuthStore((s) => s.clearMustChangePassword);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Estado para cambio de contraseña obligatorio
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Complete todos los campos");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      // Si mustChangePassword es true, el store lo setea y no navegamos
      // El componente se re-renderiza mostrando el formulario de cambio
      const store = useAuthStore.getState();
      if (!store.mustChangePassword) {
        navigate({ to: "/desktop" });
      }
    } catch {
      setError("Usuario o contraseña incorrectos");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || !confirmPassword) {
      setError("Complete todos los campos");
      return;
    }
    if (newPassword.length < 6) {
      setError("La nueva contraseña debe tener al menos 6 caracteres");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    if (newPassword === password) {
      setError("La nueva contraseña debe ser diferente a la temporal");
      return;
    }
    setError("");
    setChangingPassword(true);
    try {
      await invoke("api_change_password", {
        currentPassword: password,
        newPassword,
      });
      clearMustChangePassword();
      navigate({ to: "/desktop" });
    } catch (err) {
      setError(`Error al cambiar contraseña: ${err}`);
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <div className="flex h-full items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950">
      {/* Background pattern */}
      <div className="pointer-events-none absolute inset-0 opacity-5">
        <div
          className="h-full w-full"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "40px 40px",
          }}
        />
      </div>

      <Card className="relative w-full max-w-sm border-white/10 bg-white/5 shadow-2xl backdrop-blur-xl">
        <CardHeader className="text-center pb-2">
          {/* Logo */}
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-white/10">
            {mustChangePassword ? (
              <KeyRound className="h-10 w-10 text-amber-400" strokeWidth={1.5} />
            ) : (
              <Cross className="h-10 w-10 text-indigo-400" strokeWidth={1.5} />
            )}
          </div>

          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-white/30">
              Centro Clínico de Especialidades
            </p>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              LabSim
            </h1>
            {mustChangePassword ? (
              <p className="text-xs text-amber-400/80">
                Debe establecer una nueva contraseña
              </p>
            ) : (
              <p className="text-xs text-white/40">
                Plataforma de Simulación Clínica v3.0
              </p>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {mustChangePassword ? (
            /* Formulario de cambio de contraseña obligatorio */
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                <p className="text-xs text-amber-300/80 text-center">
                  Su contraseña es temporal. Por seguridad, elija una contraseña personal antes de continuar.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-white/70">
                  Nueva contraseña
                </Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="border-white/10 bg-white/5 text-white placeholder:text-white/30 focus:border-amber-400"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password" className="text-white/70">
                  Confirmar contraseña
                </Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="Repita la contraseña"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="border-white/10 bg-white/5 text-white placeholder:text-white/30 focus:border-amber-400"
                />
              </div>

              {error && (
                <p className="text-center text-sm text-red-400">{error}</p>
              )}

              <Button
                type="submit"
                className="w-full bg-amber-600 text-white hover:bg-amber-500"
                size="lg"
                disabled={changingPassword}
              >
                {changingPassword ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                {changingPassword ? "Guardando..." : "Establecer contraseña"}
              </Button>
            </form>
          ) : (
            /* Formulario de login normal */
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-white/70">
                  Usuario
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Ingrese su usuario"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="border-white/10 bg-white/5 text-white placeholder:text-white/30 focus:border-indigo-400"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-white/70">
                  Contraseña
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="border-white/10 bg-white/5 text-white placeholder:text-white/30 focus:border-indigo-400"
                />
              </div>

              {error && (
                <p className="text-center text-sm text-red-400">{error}</p>
              )}

              <Button
                type="submit"
                className="w-full bg-indigo-600 text-white hover:bg-indigo-500"
                size="lg"
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                {loading ? "Ingresando..." : "Iniciar Sesión"}
              </Button>
            </form>
          )}

          <p className="mt-4 text-center text-[10px] text-white/20">
            Nicolás Baier Quezada
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
