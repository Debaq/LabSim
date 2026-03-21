/**
 * LabSim Admin Panel — JavaScript
 */

// ─── Modal helpers ─────────────────────────────────

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// Cerrar modal al hacer clic fuera
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// ─── Confirmación de acciones peligrosas ───────────

document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
        if (!confirm(el.dataset.confirm)) {
            e.preventDefault();
        }
    });
});

// ─── Fetch helper para API calls desde el panel ────

async function apiCall(endpoint, options = {}) {
    const token = getCookie('labsim_admin_token');
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
    };

    const response = await fetch(`../api/index.php?route=${endpoint}`, {
        ...defaults,
        ...options,
        headers: { ...defaults.headers, ...options.headers },
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || 'Error en la solicitud');
    }

    return data;
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
}

// ─── Formateo de fechas ────────────────────────────

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-ES', {
        year: 'numeric', month: 'short', day: 'numeric'
    });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-ES', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatDuration(secs) {
    if (!secs && secs !== 0) return '—';
    secs = Math.round(secs);
    if (secs < 60) return `${secs}s`;
    if (secs < 3600) return `${Math.floor(secs / 60)}m ${secs % 60}s`;
    return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`;
}

// ─── Filtros automáticos ───────────────────────────

document.querySelectorAll('.auto-filter').forEach(el => {
    el.addEventListener('change', () => {
        el.closest('form').submit();
    });
});

// ─── Toggle JSON viewer ────────────────────────────

document.querySelectorAll('.toggle-json').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = document.getElementById(btn.dataset.target);
        if (target) {
            target.style.display = target.style.display === 'none' ? 'block' : 'none';
        }
    });
});

// ─── Flash messages auto-hide ──────────────────────

document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.5s';
        setTimeout(() => alert.remove(), 500);
    }, 5000);
});
