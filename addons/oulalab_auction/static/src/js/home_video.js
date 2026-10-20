/* Portada: arranca los videos de fondo.
   El atributo muted del HTML no siempre basta: Firefox y Safari deciden el
   autoplay leyendo la propiedad del elemento, que hay que fijar desde JS. */
(function () {
    "use strict";

    function boot() {
        var videos = document.querySelectorAll(".oulalab-home video");
        if (!videos.length) {
            return;
        }
        videos.forEach(function (video) {
            video.muted = true;
            video.defaultMuted = true;
            video.playsInline = true;
            var attempt = video.play();
            if (attempt && typeof attempt.catch === "function") {
                // Si el navegador lo rechaza igual, queda el poster: no se rompe nada.
                attempt.catch(function () {});
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
