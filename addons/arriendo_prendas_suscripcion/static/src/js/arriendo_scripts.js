odoo.define('arriendo_prendas_suscripcion.arriendo_scripts', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.RentalCatalogWidget = publicWidget.Widget.extend({
        selector: '.o_rental_catalog',

        events: {
            'change .product-selector-checkbox': '_onSelectionChange',
        },

        /**
         * Called when widget is initialized and selector is matched in DOM
         */
        start: function () {
            this.$counter = this.$('.selection_counter');
            this.$submitButton = this.$('button[type="submit"]');
            this.$checkboxes = this.$('.product-selector-checkbox');

            // Selection limit comes from a data attribute on the main container
            this.selectionLimit = parseInt(this.$el.data('selection-limit') || '0', 10);

            if (!this.$counter.length || !this.$submitButton.length) {
                console.warn("[Arriendo Catalog] HTML elements missing: .selection_counter or submit button not found.");
                return this._super.apply(this, arguments);
            }

            this._updateUI();

            return this._super.apply(this, arguments);
        },

        /**
         * Triggered when checkbox selection changes
         */
        _onSelectionChange: function (ev) {
            const selectedCount = this.$checkboxes.filter(':checked').length;

            if (selectedCount > this.selectionLimit) {
                // If limit is exceeded, deselect the newly checked box and show alert
                $(ev.currentTarget).prop('checked', false);
                this._flashLimitWarning();
                return;
            }

            this._updateUI();
        },

        /**
         * Update selection counter and button state
         */
        _updateUI: function () {
            const selectedCount = this.$checkboxes.filter(':checked').length;

            // Update text counter
            if (this.$counter.length) {
                this.$counter
                    .text(`${selectedCount} / ${this.selectionLimit} seleccionadas`)
                    .toggleClass('text-danger', selectedCount > this.selectionLimit);
            }

            // Enable or disable submit button
            if (this.$submitButton.length) {
                const disable = selectedCount === 0 || selectedCount > this.selectionLimit;
                this.$submitButton.prop('disabled', disable);
            }
        },

        /**
         * Simple visual alert when selection exceeds the limit
         */
        _flashLimitWarning: function () {
            const $warning = $('<div class="alert alert-warning text-center mt-3">Has alcanzado el límite de selección.</div>');
            this.$el.find('.alert').remove(); // remove previous alerts
            this.$el.prepend($warning);

            setTimeout(() => {
                $warning.fadeOut(500, () => $warning.remove());
            }, 2500);
        },
    });

    return publicWidget.registry.RentalCatalogWidget;
});
