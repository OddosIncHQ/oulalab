<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="liquidation_auction_view_list" model="ir.ui.view">
        <field name="name">liquidation.auction.list</field>
        <field name="model">liquidation.auction</field>
        <field name="arch" type="xml">
            <list string="Subastas" decoration-success="state == 'sold'"
                  decoration-muted="state in ('unsold','cancelled')"
                  decoration-bf="state == 'live'">
                <field name="name"/>
                <field name="product_id"/>
                <field name="reserve_price"/>
                <field name="highest_amount"/>
                <field name="bid_count"/>
                <field name="start_date"/>
                <field name="end_date"/>
                <field name="state" widget="badge"/>
                <field name="currency_id" column_invisible="1"/>
            </list>
        </field>
    </record>

    <record id="liquidation_auction_view_form" model="ir.ui.view">
        <field name="name">liquidation.auction.form</field>
        <field name="model">liquidation.auction</field>
        <field name="arch" type="xml">
            <form string="Subasta">
                <header>
                    <button name="action_publish" type="object" string="Publicar"
                            class="btn-primary" invisible="state != 'draft'"/>
                    <button name="action_cancel" type="object" string="Cancelar"
                            invisible="state not in ('draft','published')"/>
                    <button name="action_back_to_draft" type="object" string="Volver a borrador"
                            invisible="state not in ('published','cancelled')"/>
                    <button name="action_view_order" type="object" string="Ver pedido"
                            class="btn-secondary" invisible="not sale_order_id"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,published,live,sold"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box"/>
                    <field name="image_128" widget="image" class="oe_avatar"/>
                    <div class="oe_title">
                        <h1><field name="name" readonly="1"/></h1>
                    </div>
                    <group>
                        <group string="Prenda">
                            <field name="product_id"
                                   readonly="state not in ('draft','published')"/>
                            <field name="barcode"/>
                            <field name="reason"/>
                        </group>
                        <group string="Precios">
                            <field name="currency_id" groups="base.group_multi_currency"/>
                            <field name="reserve_price"/>
                            <field name="min_increment"/>
                            <field name="member_increment_pct"/>
                            <field name="public_increment_pct"/>
                        </group>
                    </group>
                    <group>
                        <group string="Temporización">
                            <field name="start_date"
                                   readonly="state not in ('draft','published')"/>
                            <field name="member_preview_hours"/>
                            <field name="public_start" readonly="1"/>
                            <field name="end_date"/>
                            <field name="anti_sniping_minutes"/>
                        </group>
                        <group string="Resultado">
                            <field name="highest_amount"/>
                            <field name="bid_count"/>
                            <field name="winner_id"/>
                            <field name="sale_order_id"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Descripción pública">
                            <field name="description"/>
                        </page>
                        <page string="Pujas">
                            <field name="bid_ids" readonly="1">
                                <list default_order="amount desc">
                                    <field name="partner_id"/>
                                    <field name="amount"/>
                                    <field name="is_member" widget="boolean_toggle"/>
                                    <field name="create_date"/>
                                    <field name="currency_id" column_invisible="1"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>
                <chatter/>
            </form>
        </field>
    </record>

    <record id="liquidation_auction_action" model="ir.actions.act_window">
        <field name="name">Subastas</field>
        <field name="res_model">liquidation.auction</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
