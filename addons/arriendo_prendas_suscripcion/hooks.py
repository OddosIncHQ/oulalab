# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    """
    Este hook se ejecuta después de que el módulo se instala.
    Configura la próxima ejecución del cron al primer día del mes siguiente.
    La firma de esta función (cr, registry) es la correcta para Odoo 18.
    """
    # Se crea una instancia del entorno de Odoo a partir del cursor y el registro.
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Se busca el cron job por su ID externo.
    cron = env.ref('arriendo_prendas_suscripcion.ir_cron_reset_monthly_subscription_changes', raise_if_not_found=False)
    
    if cron:
        # Se calcula la fecha para la primera ejecución.
        now = datetime.now()
        next_month = now + relativedelta(months=1)
        nextcall = next_month.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        
        # Se asigna la nueva fecha de ejecución.
        cron.nextcall = nextcall
