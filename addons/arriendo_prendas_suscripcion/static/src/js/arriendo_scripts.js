odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        // CORRECCIÓN: Usamos una clase contenedora. El widget solo se activará en la página del catálogo.
        selector: '.o_rental_catalog', 
        
        events: {
            'change .product-selector-checkbox': '_onSelectionChange',
        },

        /**
         * El método start solo es llamado por Odoo si el 'selector' se encuentra en la página actual.
         */
        start: function () {
            // Guardamos referencias a los elementos que vamos a manipular.
            this.$counter = this.$('.selection_counter');
            this.$submitButton = this.$('button[type="submit"]');

            // CORRECCIÓN: Comprobamos si los elementos necesarios están presentes antes de continuar.
            // Esto previene errores si el script se carga en una página incorrecta.
            if (!this.$counter.length || !this.$submitButton.length) {
                console.warn("Widget del Catálogo de Arriendo: No se encontró un elemento requerido (.selection_counter o el botón de envío). El widget no se activará.");
                return this._super.apply(this, arguments);
            }

            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);
            
            // Actualización inicial del contador y del estado del botón.
            this._updateUI();
            
            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Manejadores de Eventos
        //--------------------------------------------------------------------------

        /**
         * Se llama cada vez que un checkbox de selección de producto cambia.
         * @private
         */
        _onSelectionChange: function () {
            this._updateUI();
        },

        //--------------------------------------------------------------------------
        // Métodos Privados
        //--------------------------------------------------------------------------

        /**
         * CORRECCIÓN: Método centralizado para actualizar la interfaz de usuario.
         * Esto hace el código más limpio y seguro.
         * @private
         */
        _updateUI: function () {
            const selectedCount = this.$('.product-selector-checkbox:checked').length;
            
            // --- Actualizar Texto del Contador ---
            // Esta comprobación previene el error "Cannot set properties of null".
            if (this.$counter.length) {
                this.$counter.text(selectedCount + ' / ' + this.selectionLimit + ' seleccionadas');

                // Añade o quita una clase de advertencia según el límite de selección.
                this.$counter.toggleClass('text-danger', selectedCount > this.selectionLimit);
            }

            // --- Actualizar Estado del Botón de Envío ---
            if (this.$submitButton.length) {
                // Deshabilita el botón si no hay nada seleccionado o si se excede el límite.
                const isDisabled = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', isDisabled);
            }
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
