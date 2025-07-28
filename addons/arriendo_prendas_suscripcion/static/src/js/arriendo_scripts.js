odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        selector: '.o_rental_catalog:has(.selection-counter)',

        events: {
            'change .product-selector-checkbox': '_onSelectionChange',
        },

        /**
         * Se ejecuta al iniciar el widget cuando encuentra el selector.
         */
        start: function () {
            this.$counter = this.$('.selection-counter');
            this.$submitButton = this.$('button[type="submit"]');
            this.$checkboxes = this.$('.product-selector-checkbox');
            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);

            if (!this.$counter.length || !this.$submitButton.length || !this.$checkboxes.length) {
                console.warn("[RentalCatalogWidget] DOM incompleto. Widget no iniciado.");
                return Promise.resolve();
            }

            this._updateUI();
            return this._super.apply(this, arguments);
        },

        /**
         * Llamado cada vez que cambia un checkbox de selección.
         */
        _onSelectionChange: function (ev) {
            const selectedCount = this.$checkboxes.filter(':checked').length;

            if (selectedCount > this.selectionLimit) {
                $(ev.currentTarget).prop('checked', false);
                this._flashLimitWarning();
                return;
            }

            this._updateUI();
        },

        /**
         * Actualiza el contador y estado del botón.
         */
        _updateUI: function () {
            const selectedCount = this.$checkboxes.filter(':checked').length;

            if (this.$counter && this.$counter.length) {
                this.$counter
                    .text(`${selectedCount} / ${this.selectionLimit} seleccionadas`)
                    .toggleClass('text-danger', selectedCount > this.selectionLimit);
            }

            if (this.$submitButton && this.$submitButton.length) {
                const disable = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', disable);
            }
        },

        /**
         * Muestra una advertencia cuando se supera el límite.
         */
        _flashLimitWarning: function () {
            const $warning = $('<div class="alert alert-warning text-center mt-2" role="alert">Has alcanzado el límite de selección.</div>');

            this.$el.find('.alert.alert-warning').remove();
            this.$el.find('.selection-counter-bar').after($warning);

            setTimeout(() => {
                $warning.fadeOut(400, () => $warning.remove());
            }, 2500);
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
