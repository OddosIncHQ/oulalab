odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        // Este widget solo se activará en elementos con esta clase, que pondremos en la plantilla.
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
                console.warn("Widget del Catálogo de Arriendo: Faltan elementos requeridos.");
                return this._super.apply(this, arguments);
            }

            // Lee el límite de prendas que puede seleccionar el cliente.
            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);
            
            this._updateUI();
            
            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Manejadores de Eventos
        //--------------------------------------------------------------------------

        _onSelectionChange: function () {
            this._updateUI();
        },

        //--------------------------------------------------------------------------
        // Métodos Privados
        //--------------------------------------------------------------------------

        _updateUI: function () {
            const selectedCount = this.$('.product-selector-checkbox:checked').length;
            
            // Actualiza el texto del contador.
            if (this.$counter.length) {
                this.$counter.text(selectedCount + ' / ' + this.selectionLimit + ' seleccionadas');
                this.$counter.toggleClass('text-danger', selectedCount > this.selectionLimit);
            }

            // CORRECCIÓN CLAVE: Habilita o deshabilita el botón.
            if (this.$submitButton.length) {
                // El botón se habilita si se ha seleccionado al menos 1 prenda y no se ha superado el límite.
                const isDisabled = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', isDisabled);
            }
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
