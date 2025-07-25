odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.ArriendoCatalogo = publicWidget.Widget.extend({
        selector: '#rentForm',

        events: {
            'change input[type="checkbox"][name="product_ids"]': '_onToggleProduct',
            'submit': '_onSubmitForm',
        },

        start: function () {
            const res = this._super.apply(this, arguments);

            this.selectionCount = this.$('input[type="checkbox"][name="product_ids"]:checked').length;
            this.maxAllowed = parseInt(this.$el.data('max-allowed') || 0);

            this._createToast();
            this._updateSelectionCounter();

            return res;
        },

        _onToggleProduct: function (ev) {
            const checkbox = $(ev.currentTarget);

            if (checkbox.prop('checked')) {
                this.selectionCount++;
            } else {
                this.selectionCount--;
            }

            if (this.selectionCount > this.maxAllowed) {
                this._showToast('danger', `Has superado el máximo de ${this.maxAllowed} prendas permitidas.`);
                checkbox.prop('checked', false);
                this.selectionCount--;
            }

            this._updateSelectionCounter();
        },

        _updateSelectionCounter: function () {
            const counter = this.$('.selection-counter');
            if (counter.length > 0) {
                counter.text(`Prendas seleccionadas: ${this.selectionCount}`);
            }
        },

        _onSubmitForm: function (ev) {
            if (this.selectionCount === 0) {
                ev.preventDefault();
                this._showToast('warning', 'Debes seleccionar al menos una prenda para arrendar.');
            }
        },

        _createToast: function () {
            // Elimina toasts previos si existieran
            $('#arriendoToast').remove();

            const toastHtml = `
                <div id="arriendoToast" class="toast position-fixed bottom-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
                    <div class="toast-header">
                        <strong class="me-auto">Notificación</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Cerrar"></button>
                    </div>
                    <div class="toast-body" id="arriendo-toast-msg">Mensaje</div>
                </div>`;

            $('body').append(toastHtml);

            this.toastElement = document.getElementById('arriendoToast');
            if (this.toastElement) {
                this.bsToast = new bootstrap.Toast(this.toastElement);
            }
        },

        _showToast: function (type, message) {
            if (!this.toastElement || !this.bsToast) {
                console.warn("❗ Toast no está inicializado correctamente.");
                return;
            }

            // Actualiza clases y texto de mensaje
            $(this.toastElement)
                .removeClass('bg-success bg-danger bg-warning bg-info text-white')
                .addClass(`bg-${type} text-white`);

            const msgEl = document.getElementById('arriendo-toast-msg');
            if (msgEl) {
                msgEl.textContent = message;
                this.bsToast.show();
            } else {
                console.warn("❗ Elemento del cuerpo del toast no encontrado.");
            }
        },
    });

    return publicWidget.registry.ArriendoCatalogo;
});
