/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { mount } from "@web/core/utils/components";

export class RentalCatalog extends Component {
    static template = "arriendo_prendas_suscripcion.RentalCatalog";

    setup() {
        this.state = useState({
            selectionCount: 0,
            selectionLimit: parseInt(this.props.selectionLimit || "0", 10),
        });

        onMounted(() => {
            this.updateSelectionCount();
        });
    }

    updateSelectionCount() {
        const checked = this.el.querySelectorAll(".product-selector-checkbox:checked");
        this.state.selectionCount = checked.length;
    }

    onChange(ev) {
        const checked = this.el.querySelectorAll(".product-selector-checkbox:checked");

        if (checked.length > this.state.selectionLimit) {
            ev.target.checked = false;
            this.flashLimitWarning();
            return;
        }

        this.state.selectionCount = checked.length;
    }

    flashLimitWarning() {
        const bar = this.el.querySelector(".selection-counter-bar");
        const alert = document.createElement("div");
        alert.className = "alert alert-warning text-center mt-2";
        alert.role = "alert";
        alert.innerText = "Has alcanzado el límite de selección.";

        bar.after(alert);
        setTimeout(() => {
            alert.remove();
        }, 2500);
    }

    get disableSubmit() {
        return (
            this.state.selectionCount === 0 ||
            this.state.selectionCount > this.state.selectionLimit
        );
    }
}

// Mount the component on DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".o_rental_catalog").forEach((el) => {
        const selectionLimit = el.dataset.selectionLimit || "0";
        mount(RentalCatalog, {
            target: el,
            props: { selectionLimit },
        });
    });
});
