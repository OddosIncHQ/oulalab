/* Página /app: guía paso a paso para dejar OulaLab en la pantalla de inicio.
   Ningún navegador permite que la página cree el acceso directo por sí sola:
   en iOS lo hace Safari desde Compartir y en Android desde el menú del
   navegador. Esta página solo acompaña a la persona en esos pasos. */
(function () {
    "use strict";

    var GUIDES = {
        "ios:safari": {
            title: "En tu iPhone con Safari",
            demo: "bottom",
            steps: [
                "Abre <strong>mobile.oulalab.com</strong> en Safari con el botón de abajo.",
                "Toca el ícono de <strong>Compartir</strong>: el cuadrado con la flecha hacia arriba, en la barra inferior.",
                "Desliza la lista hacia abajo y elige <strong>Añadir a pantalla de inicio</strong>.",
                "Toca <strong>Añadir</strong> arriba a la derecha. El ícono de OulaLab queda junto a tus otras apps.",
            ],
            note: "Si no ves el ícono de Compartir, toca una vez el centro de la pantalla: la barra aparece al desplazarte hacia arriba.",
        },
        "ios:other-ios": {
            title: "Cambia a Safari primero",
            demo: null,
            steps: [
                "En iPhone, solo Safari puede agregar un sitio a la pantalla de inicio. Chrome, Instagram y Gmail no tienen esa opción.",
                "Toca el botón de abajo para abrir OulaLab y, si el sitio se abre dentro de otra aplicación, busca la opción <strong>Abrir en Safari</strong> en el menú de esa aplicación.",
                "Ya en Safari, toca <strong>Compartir</strong> y luego <strong>Añadir a pantalla de inicio</strong>.",
            ],
            note: "Si el menú no ofrece Safari, copia la dirección mobile.oulalab.com y pégala directamente en Safari.",
        },
        "android:chrome": {
            title: "En tu Android con Chrome",
            demo: "top",
            steps: [
                "Abre <strong>mobile.oulalab.com</strong> en Chrome con el botón de abajo.",
                "Toca los <strong>tres puntos</strong> de la esquina superior derecha.",
                "Elige <strong>Instalar aplicación</strong>, o <strong>Añadir a pantalla principal</strong> si aparece con ese nombre.",
                "Confirma con <strong>Instalar</strong> o <strong>Añadir</strong>.",
            ],
            note: "Chrome a veces muestra solo da la opción de añadir un acceso directo: sirve igual y queda como ícono en tu pantalla.",
        },
        "android:samsung": {
            title: "En tu Galaxy con Samsung Internet",
            demo: "bottom",
            steps: [
                "Abre <strong>mobile.oulalab.com</strong> con el botón de abajo.",
                "Toca las <strong>tres líneas</strong> de la barra inferior.",
                "Elige <strong>Añadir página a</strong> y luego <strong>Pantalla de inicio</strong>.",
                "Confirma con <strong>Añadir</strong>.",
            ],
            note: null,
        },
        "android:other-android": {
            title: "En tu Android",
            demo: "top",
            steps: [
                "Abre <strong>mobile.oulalab.com</strong> con el botón de abajo.",
                "Abre el <strong>menú</strong> de tu navegador: suele ser tres puntos o tres líneas, arriba o abajo a la derecha.",
                "Busca una opción que diga <strong>Instalar</strong>, <strong>Añadir a pantalla de inicio</strong> o <strong>Añadir acceso directo</strong>.",
                "Confirma y listo.",
            ],
            note: "Si tu navegador no tiene ninguna de esas opciones, instala Chrome y repite los pasos ahí.",
        },
        "desktop:": {
            title: "En tu computador",
            demo: null,
            steps: [
                "Abre <strong>mobile.oulalab.com</strong> con el botón de abajo.",
                "En Chrome o Edge, busca el ícono de <strong>instalar</strong> al final de la barra de direcciones, o entra al menú y elige <strong>Instalar</strong>.",
                "En Safari para Mac, usa <strong>Archivo</strong> y luego <strong>Añadir al Dock</strong>.",
            ],
            note: "También puedes dejarlo como marcador. La pantalla de inicio existe solo en teléfonos y tablets.",
        },
    };

    function detectDevice() {
        var ua = navigator.userAgent || "";
        if (/iPhone|iPad|iPod/i.test(ua)) {
            return "ios";
        }
        if (/Android/i.test(ua)) {
            return "android";
        }
        return "desktop";
    }

    function init(root) {
        var steps = {};
        root.querySelectorAll("[data-oai-step]").forEach(function (el) {
            steps[el.dataset.oaiStep] = el;
        });

        var state = {device: null};

        function show(name) {
            Object.keys(steps).forEach(function (key) {
                steps[key].classList.toggle("d-none", key !== name);
            });
            steps[name].scrollIntoView({block: "nearest", behavior: "smooth"});
        }

        function renderGuide(key) {
            var guide = GUIDES[key];
            if (!guide) {
                return;
            }
            root.querySelector("[data-oai-guide-title]").textContent = guide.title;

            var list = root.querySelector("[data-oai-guide-steps]");
            list.innerHTML = "";
            guide.steps.forEach(function (text) {
                var li = document.createElement("li");
                li.innerHTML = text;
                list.appendChild(li);
            });

            var note = root.querySelector("[data-oai-guide-note]");
            note.innerHTML = guide.note || "";
            note.classList.toggle("d-none", !guide.note);

            var phone = root.querySelector("[data-oai-demo]");
            var demoWrap = phone.closest(".oai-demo");
            if (guide.demo) {
                phone.dataset.oaiDemo = guide.demo;
                demoWrap.classList.remove("d-none");
            } else {
                demoWrap.classList.add("d-none");
            }

            show("guide");
        }

        // Dispositivo
        root.querySelectorAll("[data-oai-device]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                state.device = btn.dataset.oaiDevice;
                if (state.device === "desktop") {
                    renderGuide("desktop:");
                    return;
                }
                root.querySelectorAll("[data-oai-browsers]").forEach(function (group) {
                    group.classList.toggle("d-none", group.dataset.oaiBrowsers !== state.device);
                });
                show("browser");
            });
        });

        // Navegador
        root.querySelectorAll("[data-oai-browser]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                renderGuide(state.device + ":" + btn.dataset.oaiBrowser);
            });
        });

        // Volver
        root.querySelectorAll("[data-oai-back]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                show(btn.dataset.oaiBack);
            });
        });

        // Deja preseleccionado el dispositivo probable, sin saltarse la elección:
        // la detección falla a menudo y la persona debe poder corregirla.
        var likely = detectDevice();
        var hint = root.querySelector('[data-oai-device="' + likely + '"]');
        if (hint) {
            hint.classList.add("oai-choice--likely");
            hint.focus({preventScroll: true});
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var root = document.querySelector(".oulalab-app-install");
        if (root) {
            init(root);
        }
    });
})();
