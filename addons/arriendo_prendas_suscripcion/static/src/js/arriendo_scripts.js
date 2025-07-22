odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    // Importar jQuery si es necesario, aunque publicWidget ya lo provee como this.$el
    // const $ = require('jquery'); // No es estrictamente necesario si usas this.$()

    /**
     * Widget para gestionar la selección de prendas en el catálogo de arriendo.
     * Controla el límite de prendas permitidas y muestra notificaciones.
     */
    publicWidget.registry.ArriendoCatalogo = publicWidget.Widget.extend({
        // Selector principal del widget, debe apuntar al formulario de selección de prendas.
        // Asegúrate de que tu plantilla XML del catálogo tenga un formulario con id="rentForm".
        selector: '#rentForm', 
        
        // Eventos que el widget escuchará dentro de su selector.
        events: {
            'change input[type="checkbox"][name="product_ids"]': '_onToggleProduct',
            'submit': '_onSubmitForm',
        },

        /**
         * Método de inicialización del widget. Se ejecuta cuando el DOM está listo.
         */
        start: function () {
            // Llama al método start de la clase padre.
            const res = this._super.apply(this, arguments);

            // Inicializa el contador de prendas seleccionadas.
            // Contar las checkboxes que ya están marcadas al inicio (útil si hay preselección).
            this.selectionCount = this.$('input[type="checkbox"][name="product_ids"]:checked').length;
            
            // Obtener el límite máximo de prendas permitidas desde un atributo de datos del formulario.
            // Es más robusto que un campo oculto, ya que el valor siempre está disponible en el elemento raíz del widget.
            // Asegúrate de que tu formulario en la plantilla QWeb tenga un atributo data-max-allowed.
            this.maxAllowed = parseInt(this.$el.data('max-allowed') || 0);

            // Crear el elemento Toast una vez al inicio.
            this._createToast();
            // Actualizar el contador en la UI al inicio.
            this._updateSelectionCounter();

            return res;
        },

        /**
         * Maneja el evento de cambio (marcar/desmarcar) en los checkboxes de productos.
         * @param {Event} ev - El evento de cambio.
         */
        _onToggleProduct: function (ev) {
            const checkbox = $(ev.currentTarget); // El checkbox que disparó el evento.
            
            if (checkbox.prop('checked')) {
                // Si se marcó el checkbox, incrementa el contador.
                this.selectionCount++;
            } else {
                // Si se desmarcó el checkbox, decrementa el contador.
                this.selectionCount--;
            }

            // Validar si se ha superado el límite permitido.
            if (this.selectionCount > this.maxAllowed) {
                // Si se excede el límite, revertir la selección y mostrar un mensaje de error.
                this._showToast('danger', `Has superado el máximo de ${this.maxAllowed} prendas permitidas.`);
                checkbox.prop('checked', false); // Desmarcar el checkbox.
                this.selectionCount--; // Revertir el incremento.
            }

            // Actualizar el texto del contador en la interfaz de usuario.
            this._updateSelectionCounter();
        },

        /**
         * Actualiza el texto del contador de selección en la UI.
         */
        _updateSelectionCounter: function() {
            // Asegúrate de que exista un elemento con la clase 'selection-counter' en tu plantilla.
            this.$('.selection-counter').text(`Prendas seleccionadas: ${this.selectionCount}`);
        },

        /**
         * Maneja el evento de envío del formulario.
         * @param {Event} ev - El evento de envío.
         */
        _onSubmitForm: function (ev) {
            // Validar que se haya seleccionado al menos una prenda antes de enviar.
            if (this.selectionCount === 0) {
                ev.preventDefault(); // Prevenir el envío del formulario.
                this._showToast('warning', 'Debes seleccionar al menos una prenda para arrendar.');
            }
            // Aquí podrías añadir más validaciones si es necesario antes del envío al servidor.
        },

        /**
         * Crea el elemento HTML para el Toast y lo añade al cuerpo del documento.
         * Utiliza la estructura de Toast de Bootstrap 5.
         */
        _createToast: function () {
            // Eliminar cualquier toast existente para evitar duplicados.
            $('#arriendoToast').remove(); 

            const toastHtml = `
                <div id="arriendoToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
                    <div class="toast-header">
                        <strong class="me-auto">Notificación</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                    <div class="toast-body" id="arriendo-toast-msg"></div>
                </div>`;
            
            // Añadir el toast al final del cuerpo del documento.
            $('body').append(toastHtml);
            
            // Obtener la instancia del toast de Bootstrap 5.
            this.toastElement = document.getElementById('arriendoToast');
            this.bsToast = new bootstrap.Toast(this.toastElement);
        },

        /**
         * Muestra un mensaje Toast con un tipo de estilo específico.
         * @param {string} type - El tipo de mensaje (e.g., 'success', 'danger', 'warning', 'info').
         * @param {string} message - El mensaje a mostrar.
         */
        _showToast: function (type, message) {
            // Remover clases de color anteriores y añadir la nueva.
            $(this.toastElement).removeClass('bg-success bg-danger bg-warning bg-info text-white').addClass(`bg-${type} text-white`);
            
            // Actualizar el mensaje en el cuerpo del toast.
            $('#arriendo-toast-msg').text(message);
            
            // Mostrar el toast.
            this.bsToast.show();
        }
    });

    // Registrar el widget para que Odoo lo inicialice automáticamente.
    return publicWidget.registry.ArriendoCatalogo;
});
