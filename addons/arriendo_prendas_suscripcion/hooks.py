# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, SUPERUSER_ID

def post_init_hook(env):
    """
    Este hook se ejecuta después de que el módulo se instala.
    Configura la próxima ejecución del cron al primer día del mes siguiente.
    La firma de esta función (env) se ajusta al método de llamada del servidor.
    """
    # Se busca el cron job por su ID externo usando el entorno (env) proporcionado.
    cron = env.ref('arriendo_prendas_suscripcion.ir_cron_reset_monthly_subscription_changes', raise_if_not_found=False)
    
    if cron:
        # Se calcula la fecha para la primera ejecución.
        now = datetime.now()
        next_month = now + relativedelta(months=1)
        nextcall = next_month.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        
        # Se asigna la nueva fecha de ejecución.
        cron.nextcall = nextcall
