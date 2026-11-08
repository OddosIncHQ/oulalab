/* OulaLab — Prendas en venta: carrito y checkout. Vanilla JS (web.assets_frontend). */
(function () {
    "use strict";

    function jsonrpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params || {},
                                   id: Math.floor(Math.random() * 1e9) }),
        }).then(function (r) { return r.json(); }).then(function (data) {
            if (data.error) throw new Error((data.error.data && data.error.data.message) || "Error");
            return data.result;
        });
    }

    function clp(n) {
        return "$" + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function setCount(count) {
        document.querySelectorAll(".olx-cart-count").forEach(function (el) {
            el.textContent = count;
            el.dataset.count = count;
            el.classList.remove("is-bump");
            void el.offsetWidth;  // reinicia la animación de confirmación
            el.classList.add("is-bump");
        });
    }

    function onAdd(btn) {
        var go = btn.dataset.go;
        btn.disabled = true;
        jsonrpc("/prendas/cart/add", { item_id: Number(btn.dataset.item) }).then(function (res) {
            if (!res.ok) {
                window.alert(res.error);
                btn.disabled = false;
                return;
            }
            setCount(res.count);
            if (go) { window.location.href = go; return; }
            document.querySelectorAll('.olx-add[data-item="' + btn.dataset.item + '"]:not([data-go])')
                .forEach(function (b) { b.disabled = true; b.textContent = "En tu carrito"; });
        }).catch(function () {
            btn.disabled = false;
            window.alert("No pudimos agregar la prenda. Intenta de nuevo.");
        });
    }

    function onRemove(btn) {
        btn.disabled = true;
        jsonrpc("/prendas/cart/remove", { item_id: Number(btn.dataset.item) })
            .then(function () { window.location.reload(); })
            .catch(function () { btn.disabled = false; });
    }

    function initCheckout(form) {
        var grand = form.querySelector(".olx-grand");
        var bag = form.querySelector(".olx-bag-toggle");
        var address = form.querySelector(".olx-address");
        var base = grand ? Number(grand.dataset.base) : 0;
        var ship = grand ? Number(grand.dataset.ship) : 0;

        function mode() {
            var m = form.querySelector(".olx-mode:checked");
            return m ? m.value : "pickup";
        }
        function refresh() {
            var delivery = mode() === "delivery";
            if (address) {
                address.hidden = !delivery;
                address.querySelectorAll("#olxCommune, #olxStreet").forEach(function (el) {
                    el.required = delivery;
                });
            }
            var withBag = bag && bag.checked;
            form.querySelectorAll(".olx-bag-row").forEach(function (el) { el.hidden = !withBag; });
            form.querySelectorAll(".olx-ship-row").forEach(function (el) { el.hidden = !delivery; });
            if (grand) {
                var total = base + (withBag ? Number(bag.dataset.price) : 0) + (delivery ? ship : 0);
                grand.textContent = clp(total);
            }
        }
        form.querySelectorAll(".olx-mode").forEach(function (r) { r.addEventListener("change", refresh); });
        if (bag) bag.addEventListener("change", refresh);
        form.addEventListener("submit", function () {
            var pay = form.querySelector(".olx-pay");
            if (pay) { pay.disabled = true; pay.textContent = "Reservando tus prendas…"; }
        });
        refresh();
    }

    document.addEventListener("click", function (ev) {
        var add = ev.target.closest(".olx-add");
        if (add) { ev.preventDefault(); onAdd(add); return; }
        var rm = ev.target.closest(".olx-remove");
        if (rm) { ev.preventDefault(); onRemove(rm); }
    });

    document.addEventListener("DOMContentLoaded", function () {
        var form = document.getElementById("olxCheckout");
        if (form) initCheckout(form);
        // Miniaturas de la galería: marca la activa al cambiar de foto.
        document.querySelectorAll(".olx-gallery .carousel").forEach(function (car) {
            car.addEventListener("slid.bs.carousel", function (e) {
                var thumbs = car.parentElement.querySelectorAll(".olx-thumb");
                thumbs.forEach(function (t, i) { t.classList.toggle("active", i === e.to); });
            });
        });
    });
})();
