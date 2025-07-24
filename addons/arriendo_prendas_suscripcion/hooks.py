from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID, api

def post_init_hook(env):
    """Set next execution of cron to 1st of next month at 03:00"""
    cron = env.ref('arriendo_prendas_suscripcion.ir_cron_reset_monthly_subscription_changes', raise_if_not_found=False)
    if cron:
        now = datetime.now()
        next_month = now + relativedelta(months=1)
        nextcall = next_month.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        cron.nextcall = nextcall.strftime('%Y-%m-%d %H:%M:%S')
