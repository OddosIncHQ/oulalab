from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.api import Environment, SUPERUSER_ID

def post_init_hook(cr, registry):
    """Set nextcall del cron a la próxima fecha del mes (1° del siguiente mes a las 03:00)"""
    env = Environment(cr, SUPERUSER_ID, {})
    cron = env.ref('arriendo_prendas_suscripcion.ir_cron_reset_monthly_subscription_changes', raise_if_not_found=False)

    if cron:
        now = datetime.now()
        first_day_next_month = (now + relativedelta(months=1)).replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        cron.nextcall = first_day_next_month.strftime('%Y-%m-%d %H:%M:%S')
