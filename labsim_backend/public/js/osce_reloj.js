/*
 * Reloj del OSCE en el navegador: misma cuenta que Osce::estadoReloj() en
 * PHP (src/Osce.php). Pide el estado al servidor cada pocos segundos y
 * entremedio avanza solo con el reloj local, así la cuenta regresiva no
 * salta aunque la red ande lenta.
 *
 * Uso: OsceReloj.iniciar(url, function (datos, reloj, t) { ... });
 *   datos = respuesta de api/osce_reloj.php, reloj = {fase, vuelta, slot,
 *   restante_s} o null si no ha partido, t = segundos de reloj corridos.
 */
(function () {
    'use strict';

    function estadoReloj(cfg, t) {
        // Tiempos por vuelta: uno por estación en vueltas; en cadena, todos los turnos.
        var S = cfg.turnos || cfg.estaciones, V = cfg.vueltas, dur = cfg.duracion_s;
        var paso = dur + cfg.pausa_s;
        if (S <= 0 || V <= 0) return { fase: 'terminado', vuelta: 0, slot: 0, restante_s: 0 };
        if (t < 0) return { fase: 'antes', vuelta: 0, slot: 0, restante_s: -t };
        var largoVuelta = S * paso + cfg.pausa_vueltas_s;
        var v = Math.floor(t / largoVuelta);
        if (v >= V) return { fase: 'terminado', vuelta: V - 1, slot: S - 1, restante_s: 0 };
        var r = t - v * largoVuelta;
        var j = Math.min(Math.floor(r / paso), S - 1);
        var rr = r - j * paso;
        if (rr < dur) return { fase: 'estacion', vuelta: v, slot: j, restante_s: dur - rr };
        if (j < S - 1) return { fase: 'cambio', vuelta: v, slot: j, restante_s: paso - rr };
        if (v === V - 1) return { fase: 'terminado', vuelta: v, slot: j, restante_s: 0 };
        return { fase: 'entre_vueltas', vuelta: v, slot: j, restante_s: largoVuelta - r };
    }

    function inicioSlot(cfg, vuelta, slot) {
        var paso = cfg.duracion_s + cfg.pausa_s;
        return vuelta * ((cfg.turnos || cfg.estaciones) * paso + cfg.pausa_vueltas_s) + slot * paso;
    }

    function mmss(s) {
        s = Math.max(0, Math.ceil(s));
        var m = Math.floor(s / 60), r = s % 60;
        return m + ':' + (r < 10 ? '0' : '') + r;
    }

    function iniciar(url, alTic, cadaMs) {
        var datos = null, base = 0, baseLocal = 0;
        function pedir() {
            fetch(url, { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) {
                if (d.error) return;
                datos = d;
                base = d.transcurrido_s;
                baseLocal = performance.now();
                tic();
            }).catch(function () { /* sin red: sigue con el reloj local */ });
        }
        function tic() {
            if (!datos) return;
            var t = null, reloj = null;
            if (base !== null && base !== undefined) {
                t = datos.pausado || datos.estado !== 'en_curso' ? base : base + (performance.now() - baseLocal) / 1000;
                reloj = estadoReloj(datos.cfg, Math.floor(t));
            }
            alTic(datos, reloj, t);
        }
        pedir();
        setInterval(pedir, cadaMs || 5000);
        setInterval(tic, 250);
        return { refrescar: pedir };
    }

    window.OsceReloj = { iniciar: iniciar, estadoReloj: estadoReloj, inicioSlot: inicioSlot, mmss: mmss };
})();
