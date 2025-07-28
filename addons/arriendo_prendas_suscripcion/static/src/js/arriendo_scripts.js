odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        selector: '.o_rental_catalog',

        events: {
            'change .product-selector-checkbox': '_onSelectionChange',
        },

        /**
         * Se ejecuta cuando el widget inicia y el selector está presente.
         */
        start: function () {
            // Cache DOM elements
            this.$counter = this.$('.selection_counter');
            this.$submitButton = this.$('button[type="submit"]');

            // Validación: asegúrate de que ambos elementos existen
            if (!this.$counter.length || !this.$submitButton.length) {
                console.warn("Widget del Catálogo de Arriendo: Faltan elementos HTML requeridos. El widget no se activará en esta página.");
                return this._super.apply(this, arguments);
            }

            // Obtiene el límite de selección desde un atributo data
            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);

            this._updateUI();

            return this._super.apply(this, arguments);
        },

        _onSelectionChange: function () {
            this._updateUI();
        },

        _updateUI: function () {
            const selectedCount = this.$('.product-selector-checkbox:checked').length;

            // Verifica si el contador existe y no es null
            if (this.$counter && this.$counter.length && this.$counter.get(0)) {
                this.$counter.text(`${selectedCount} / ${this.selectionLimit} seleccionadas`);
                this.$counter.toggleClass('text-danger', selectedCount > this.selectionLimit);
            } else {
                console.warn("Elemento '.selection_counter' no disponible en este momento.");
            }

            // Verifica si el botón de envío existe y no es null
            if (this.$submitButton && this.$submitButton.length && this.$submitButton.get(0)) {
                const isDisabled = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', isDisabled);
            } else {
                console.warn("Elemento 'submit button' no disponible en este momento.");
            }
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
