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
            this.selectionCount = 0;
            this.maxAllowed = parseInt($('#max_prendas_permitidas').val() || 0);
            this._createToast();
            return this._super.apply(this, arguments);
        },

        _onToggleProduct: function (ev) {
            const checkbox = $(ev.currentTarget);
            if (checkbox.prop('checked')) {
                this.selectionCount++;
            } else {
                this.selectionCount--;
            }

            if (this.selectionCount > this.maxAllowed) {
                this._showToast('Has superado el máximo de prendas permitidas.');
                checkbox.prop('checked', false);
                this.selectionCount--;
            }

            $('.selection-counter').text(`Seleccionadas: ${this.selectionCount}`);
        },

        _onSubmitForm: function (ev) {
            if (this.selectionCount === 0) {
                ev.preventDefault();
                this._showToast('Debes seleccionar al menos una prenda para arrendar.');
            }
        },

        _createToast: function () {
            const toastHtml = `
                <div class="toast bg-danger text-white" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-body" id="arriendo-toast-msg">Mensaje</div>
                </div>`;
            $('body').append(toastHtml);
            this.toast = $('.toast');
        },

        _showToast: function (message) {
            $('#arriendo-toast-msg').text(message);
            this.toast.toast({ delay: 3000 });
            this.toast.toast('show');
        }
    });

    return publicWidget.registry.ArriendoCatalogo;
});
