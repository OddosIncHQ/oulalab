/* OulaLab Auctions — timer, live polling y envío de pujas.
   Vanilla JS registrado en web.assets_frontend. */
(function () {
    "use strict";

    // Odoo entrega datetimes como "YYYY-MM-DD HH:MM:SS" en UTC (naive).
    function parseOdooUTC(s) {
        if (!s) return null;
        return new Date(s.replace(" ", "T") + "Z");
    }

    // Llamada a una ruta type="jsonrpc" de Odoo.
    function jsonrpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
                id: Math.floor(Math.random() * 1e9),
            }),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) throw new Error(data.error.data && data.error.data.message || "Error");
                return data.result;
            });
    }

    function fmt(ms) {
        if (ms <= 0) return "Cerrada";
        var s = Math.floor(ms / 1000);
        var d = Math.floor(s / 86400); s -= d * 86400;
        var h = Math.floor(s / 3600); s -= h * 3600;
        var m = Math.floor(s / 60); s -= m * 60;
        var pad = function (n) { return String(n).padStart(2, "0"); };
        return (d > 0 ? d + "d " : "") + pad(h) + ":" + pad(m) + ":" + pad(s);
    }

    function initTimers() {
        document.querySelectorAll(".oulalab-timer").forEach(function (el) {
            var end = parseOdooUTC(el.dataset.end);
            var serverNow = parseOdooUTC(el.dataset.now);
            if (!end) return;
            // Offset entre reloj del cliente y del servidor (evita desfases).
            var offset = serverNow ? (serverNow.getTime() - Date.now()) : 0;
            var out = el.querySelector(".timer-value");

            function tick() {
                var remaining = end.getTime() - (Date.now() + offset);
                if (out) out.textContent = fmt(remaining);
                if (remaining <= 0) {
                    clearInterval(el._t);
                    var box = document.querySelector(".oulalab-bid-box");
                    if (box) box.innerHTML = '<div class="alert alert-secondary mb-0">La subasta ha cerrado.</div>';
                }
            }
            tick();
            el._t = setInterval(tick, 1000);
            el._end = end; el._offset = offset;
        });
    }

    function initDetail() {
        var root = document.querySelector(".oulalab-auction-detail");
        if (!root) return;
        var auctionId = root.dataset.auctionId;
        var btn = root.querySelector(".oulalab-bid-btn");
        var input = root.querySelector(".oulalab-bid-input");
        var feedback = root.querySelector(".oulalab-bid-feedback");
        var highestEl = root.querySelector(".oulalab-highest");
        var countEl = root.querySelector(".oulalab-bidcount");
        var minNextEl = root.querySelector(".oulalab-minnext");
        var timerEl = root.querySelector(".oulalab-timer");

        function applyState(res) {
            if (!res || !res.ok) return;
            if (highestEl) highestEl.textContent = highestEl.textContent.replace(/[\d.,]+/, Number(res.highest).toLocaleString("es-CL"));
            if (countEl) countEl.textContent = res.bid_count;
            if (minNextEl) minNextEl.textContent = minNextEl.textContent.replace(/[\d.,]+/, Number(res.min_next).toLocaleString("es-CL"));
            if (input) { input.min = res.min_next; input.dataset.min = res.min_next; }
            // Anti-sniping: el cierre puede haberse extendido.
            if (timerEl && res.end_date) {
                var newEnd = parseOdooUTC(res.end_date);
                if (newEnd) timerEl._end = newEnd;
            }
        }

        // Puja
        if (btn) {
            btn.addEventListener("click", function () {
                var amount = parseFloat(input.value);
                var min = parseFloat(input.dataset.min);
                feedback.className = "oulalab-bid-feedback small mt-2";
                if (isNaN(amount) || amount < min) {
                    feedback.classList.add("text-danger");
                    feedback.textContent = "La puja debe ser al menos " + Number(min).toLocaleString("es-CL");
                    return;
                }
                btn.disabled = true;
                jsonrpc("/auctions/" + auctionId + "/bid", { auction_id: Number(auctionId), amount: amount })
                    .then(function (res) {
                        btn.disabled = false;
                        if (res && res.ok) {
                            feedback.classList.add("text-success");
                            feedback.textContent = "¡Puja registrada!";
                            applyState(Object.assign({ ok: true }, res));
                        } else {
                            feedback.classList.add("text-danger");
                            feedback.textContent = (res && res.error) || "No se pudo registrar la puja.";
                        }
                    })
                    .catch(function (e) {
                        btn.disabled = false;
                        feedback.classList.add("text-danger");
                        feedback.textContent = e.message || "Error de red.";
                    });
            });
        }

        // Polling ligero cada 8s para reflejar pujas de otros / extensiones.
        setInterval(function () {
            jsonrpc("/auctions/" + auctionId + "/state", { auction_id: Number(auctionId) })
                .then(applyState)
                .catch(function () {});
        }, 8000);
    }

    function boot() { initTimers(); initDetail(); }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
