// Chat de prueba con el paciente (ficha Anamnesis) -- manda a
// llm_chat_test.php lo que hay AHORA MISMO en el formulario (sin guardar),
// mismo criterio con el que LlmConfig::buildSystemPrompt() arma el prompt
// real más adelante en la app. HIST_KEYS espejea CaseBuilder::HIST_CHECKBOXES.
(function () {
    var sendBtn = document.getElementById('chat-test-send');
    var resetBtn = document.getElementById('chat-test-reset');
    var input = document.getElementById('chat-test-input');
    var log = document.getElementById('chat-test-log');
    if (!sendBtn || !input || !log) return;

    var HIST_KEYS = ['hipoacusia_familiar', 'ototoxicos', 'trauma_acustico', 'otitis', 'meningitis', 'tce', 'diabetes', 'hta'];
    var history = [];
    var sending = false;

    function fieldValue(name) {
        var el = document.querySelector('[name="' + name + '"]');
        return el ? el.value : '';
    }

    function currentName() {
        var n1 = document.querySelector('[name="nombre1"]');
        if (n1) {
            var parts = [n1.value, fieldValue('nombre2'), fieldValue('apellido1'), fieldValue('apellido2')].filter(function (p) { return p; });
            if (parts.length) return parts.join(' ');
        }
        var staticName = document.getElementById('chat-static-name');
        return (staticName && staticName.value) || 'el paciente';
    }

    function currentAntecedentes() {
        var out = {};
        HIST_KEYS.forEach(function (key) {
            var el = document.querySelector('[name="hist[' + key + ']"]');
            out[key] = !!(el && el.checked);
        });
        return out;
    }

    function currentTinnitus() {
        return {
            lateralidad: fieldValue('tinnitus[lateralidad]'),
            oido: fieldValue('tinnitus[oido]'),
            predominio: fieldValue('tinnitus[predominio]'),
            ruido: fieldValue('tinnitus[ruido]'),
            frecuencia: fieldValue('tinnitus[frecuencia]'),
            pulsatil: !!document.querySelector('[name="tinnitus[pulsatil]"]:checked'),
            permanente: !!document.querySelector('[name="tinnitus[permanente]"]:checked'),
        };
    }

    function addBubble(role, text) {
        var wrap = document.createElement('div');
        wrap.style.margin = '0.4rem 0';
        var tag = document.createElement('strong');
        tag.textContent = role === 'user' ? 'Alumno: ' : (role === 'error' ? 'Error: ' : 'Paciente: ');
        tag.style.color = role === 'user' ? '#1a2744' : (role === 'error' ? '#a33' : '#2e7d32');
        var body = document.createElement('span');
        body.textContent = text;
        wrap.appendChild(tag);
        wrap.appendChild(body);
        log.appendChild(wrap);
        log.scrollTop = log.scrollHeight;
    }

    function send() {
        var message = input.value.trim();
        if (!message || sending) return;
        sending = true;
        sendBtn.disabled = true;
        addBubble('user', message);
        input.value = '';

        var payload = {
            csrf_token: document.querySelector('input[name="csrf_token"]').value,
            message: message,
            history: history,
            nombre: currentName(),
            edad: fieldValue('age'),
            genero: (document.querySelector('input[name="gender"]:checked') || {}).value || '0',
            antecedentes: currentAntecedentes(),
            medicamentos: fieldValue('medicamentos'),
            cirugias: fieldValue('cirugias'),
            otros: fieldValue('otros'),
            comportamiento: fieldValue('comportamiento'),
            disposicion: fieldValue('disposicion'),
            tinnitus: currentTinnitus(),
        };

        fetch('llm_chat_test.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(function (res) {
            return res.json().then(function (data) { return { ok: res.ok, data: data }; });
        }).then(function (result) {
            if (!result.ok || result.data.error) {
                addBubble('error', result.data.error || 'Error desconocido.');
                return;
            }
            history.push({ role: 'user', content: message });
            history.push({ role: 'assistant', content: result.data.reply });
            addBubble('assistant', result.data.reply);
        }).catch(function (err) {
            addBubble('error', 'No se pudo contactar al servidor: ' + err.message);
        }).finally(function () {
            sending = false;
            sendBtn.disabled = false;
            input.focus();
        });
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); send(); }
    });
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            history = [];
            log.innerHTML = '';
            input.focus();
            var result = document.getElementById('oirs-test-result');
            if (result) result.innerHTML = '';
        });
    }

    var oirsBtn = document.getElementById('oirs-test-btn');
    var oirsResult = document.getElementById('oirs-test-result');
    if (oirsBtn && oirsResult) {
        var VEREDICTO_LABELS = {
            reclamo: { text: 'Reclamo', color: '#a33', bg: '#fbeaea' },
            merito: { text: 'Mérito', color: '#2e7d32', bg: '#eaf6ea' },
            neutro: { text: 'Neutro (sin aviso)', color: '#666', bg: '#f0f0f0' },
        };

        oirsBtn.addEventListener('click', function () {
            oirsBtn.disabled = true;
            oirsResult.innerHTML = '<p class="legend">Evaluando…</p>';

            fetch('oirs_test.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    csrf_token: document.querySelector('input[name="csrf_token"]').value,
                    history: history,
                    disposicion: fieldValue('disposicion'),
                }),
            }).then(function (res) {
                return res.json().then(function (data) { return { ok: res.ok, data: data }; });
            }).then(function (result) {
                if (!result.ok || result.data.error) {
                    oirsResult.innerHTML = '';
                    var err = document.createElement('p');
                    err.style.color = '#a33';
                    err.textContent = result.data.error || 'Error desconocido.';
                    oirsResult.appendChild(err);
                    return;
                }
                var v = result.data;
                var style = VEREDICTO_LABELS[v.veredicto] || VEREDICTO_LABELS.neutro;
                oirsResult.innerHTML = '';

                var badge = document.createElement('span');
                badge.textContent = style.text;
                badge.style.cssText = 'display:inline-block; padding:0.15rem 0.6rem; border-radius:12px; font-weight:600; font-size:0.8rem; color:' + style.color + '; background:' + style.bg + ';';
                oirsResult.appendChild(badge);

                if (v.veredicto !== 'neutro') {
                    var mail = document.createElement('div');
                    mail.style.cssText = 'margin-top:0.5rem; padding:0.7rem; border:1px solid #e5e5e5; border-radius:6px; background:#fafafa; font-size:0.88rem;';
                    var from = document.createElement('div');
                    from.style.color = '#888';
                    from.textContent = 'De: Oficina de Informaciones, Reclamos y Sugerencias (OIRS)';
                    var subject = document.createElement('div');
                    subject.style.cssText = 'font-weight:600; margin-top:0.2rem;';
                    subject.textContent = 'Asunto: ' + v.asunto;
                    var body = document.createElement('div');
                    body.style.marginTop = '0.5rem';
                    body.style.whiteSpace = 'pre-wrap';
                    body.textContent = v.cuerpo;
                    mail.appendChild(from);
                    mail.appendChild(subject);
                    mail.appendChild(body);
                    oirsResult.appendChild(mail);
                }
            }).catch(function (err) {
                oirsResult.innerHTML = '';
                var errEl = document.createElement('p');
                errEl.style.color = '#a33';
                errEl.textContent = 'No se pudo contactar al servidor: ' + err.message;
                oirsResult.appendChild(errEl);
            }).finally(function () {
                oirsBtn.disabled = false;
            });
        });
    }
})();
