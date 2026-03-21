import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/stores/auth-store";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import { Loader2, Cross } from "lucide-react";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      navigate({ to: "/desktop" });
    } catch {
      setError("Usuario o contraseña incorrectos");
    } finally {
      setLoading(false);
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
          {/* Logo: cruz clínica estilizada */}
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-white/10">
            <Cross className="h-10 w-10 text-indigo-400" strokeWidth={1.5} />
          </div>

          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-white/30">
              Centro Clínico de Especialidades
            </p>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              LabSim
            </h1>
            <p className="text-xs text-white/40">
              Plataforma de Simulación Clínica v3.0
            </p>
          </div>
        </CardHeader>

        <CardContent>
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

          <p className="mt-4 text-center text-[10px] text-white/20">
            Nicolás Baier Quezada
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
