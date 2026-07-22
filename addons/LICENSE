# OulaLab Auction — Liquidación de prendas (Odoo 19)

Módulo de Odoo 19 que habilita una sección de **subastas** en el sitio web para
liquidar prendas retiradas del negocio de alquiler (muy usadas o fuera de
temporada), con **preferencia para socios OulaLab**.

## Características

- **Sección pública** `/auctions` con listado y detalle de cada prenda en subasta.
- **Precio mínimo (reserva):** bajo ese monto la subasta se declara desierta.
- **Temporizador de cierre** sincronizado con el reloj del servidor (no depende
  de la hora del navegador).
- **Preferencia de socio**, en dos palancas reales validadas en servidor:
  - *Ventana de preview*: los socios pujan antes que el público.
  - *Incremento asimétrico*: el socio sube con un salto porcentual menor (2% vs 5%).
- **Anti-sniping (soft close):** una puja en los minutos finales extiende el cierre.
- **Concurrencia segura:** bloqueo pesimista de fila (`SELECT ... FOR UPDATE`) para
  serializar pujas simultáneas.
- **Cierre automático** vía cron: al adjudicar, genera una cotización (`sale.order`)
  para el ganador y entra al flujo normal de venta/factura.

## Requisitos

- Odoo 19.0
- Módulos: `base`, `sale_management`, `product`, `website`

## Instalación

1. Clona el repositorio dentro de tu carpeta de *addons*:
   ```bash
   cd /ruta/a/tus/addons
   git clone https://github.com/<tu-usuario>/oulalab-auction.git
   ```
   El módulo a instalar es la carpeta `oulalab-auction/oulalab_auction`.
   Asegúrate de que la ruta padre esté en `addons_path` (odoo.conf).

2. Reinicia Odoo actualizando la lista de apps:
   ```bash
   ./odoo-bin -c odoo.conf -u all -d TU_BASE   # o -i oulalab_auction para instalar
   ```

3. En Odoo: **Apps** → quita el filtro *Apps* → busca **OulaLab Auction** → *Instalar*.

> Si prefieres que el repo contenga el módulo en la raíz (sin la carpeta
> `oulalab-auction/` intermedia), mueve `oulalab_auction/` un nivel arriba.

## Configuración

1. **Icono del menú:** reemplaza `oulalab_auction/static/description/icon.png.txt`
   por un `icon.png` real (~140×140, identidad OulaLab), o quita el atributo
   `web_icon` del `menuitem` raíz en `views/auction_menus.xml`.

2. **Detección de socio:** el campo `res.partner.is_oulalab_member` se calcula en
   `models/res_partner.py`. Por defecto se deriva de tener un `sale.order`
   confirmado — **ajústalo a tu modelo real de suscripción** (cambia el
   `@api.depends` y la condición interna).

3. **Cron:** `data/auction_cron.xml` corre cada minuto y gestiona las transiciones
   de estado (publicada → en curso → adjudicada/desierta).

## Uso

1. Menú **Subastas → Subastas → Nuevo**: elige la prenda, fija reserva, fechas,
   ventana de preview y anti-sniping.
2. Pulsa **Publicar**. El cron la pasa a *En curso* al llegar el inicio.
3. Los clientes ven `/auctions`, pujan (login requerido) y al cierre se adjudica
   automáticamente al mejor postor por sobre la reserva.

## Notas técnicas (Odoo 19)

- Vistas en sintaxis 19: `<list>` (no `<tree>`), modificadores inline
  (`invisible="..."`, sin `attrs`).
- Controladores JSON con `type="jsonrpc"` (antes `type="json"`).
- El polling en vivo es cada 8 s; para alto volumen, migrar a `bus.bus`
  (longpolling) para empujar precios en tiempo real.

## Licencia

LGPL-3. Ver [LICENSE](LICENSE).
