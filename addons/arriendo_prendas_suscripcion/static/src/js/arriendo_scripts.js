odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        // El widget solo se activará en elementos con esta clase.
        selector: '.o_rental_catalog', 
        
        events: {
            'change .product-selector-checkbox': '_onSelectionChange',
        },

        /**
         * El método start se ejecuta solo si el 'selector' se encuentra en la página.
         */
        start: function () {
            this.$counter = this.$('.selection_counter');
            this.$submitButton = this.$('button[type="submit"]');

            // Comprobación de seguridad para evitar errores.
            if (!this.$counter.length || !this.$submitButton.length) {
                console.warn("Widget del Catálogo de Arriendo: Faltan elementos HTML requeridos. El widget no se activará en esta página.");
                return this._super.apply(this, arguments);
            }

            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);
            
            this._updateUI();
            
            return this._super.apply(this, arguments);
        },

        _onSelectionChange: function () {
            this._updateUI();
        },

        _updateUI: function () {
            const selectedCount = this.$('.product-selector-checkbox:checked').length;
            
            if (this.$counter.length) {
                this.$counter.text(selectedCount + ' / ' + this.selectionLimit + ' seleccionadas');
                this.$counter.toggleClass('text-danger', selectedCount > this.selectionLimit);
            }

            if (this.$submitButton.length) {
                const isDisabled = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', isDisabled);
            }
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
