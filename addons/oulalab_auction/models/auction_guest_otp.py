import hashlib
import json
import secrets
from datetime import timedelta

from odoo import fields, models

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60


class AuctionGuestOtp(models.Model):
    """Código de verificación por correo para postores sin cuenta en Odoo.

    Demuestra que quien oferta controla el email declarado antes de que el
    postor quede asociado a un contacto (y a una dirección de despacho).
    """

    _name = "auction.guest.otp"
    _description = "Verificación por correo para postores sin cuenta"

    email = fields.Char(required=True, index=True)
    code_hash = fields.Char(required=True)
    payload = fields.Text(required=True, help="Datos del postor (JSON).")
    expires_at = fields.Datetime(required=True)
    attempts = fields.Integer(default=0)

    def _hash_code(self, email, code):
        raw = "%s|%s|%s" % (self.env.cr.dbname, email.lower(), code)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def new_code():
        return "%06d" % secrets.randbelow(1000000)

    def recently_sent(self, email):
        last = self.sudo().search(
            [("email", "=", email)], order="id desc", limit=1
        )
        if not last:
            return False
        created = last.create_date or fields.Datetime.now()
        return (fields.Datetime.now() - created).total_seconds() < OTP_RESEND_SECONDS

    def issue(self, email, payload):
        """Crea un código nuevo (invalida los anteriores) y devuelve el código."""
        self.sudo().search([("email", "=", email)]).unlink()
        code = self.new_code()
        self.sudo().create({
            "email": email,
            "code_hash": self._hash_code(email, code),
            "payload": json.dumps(payload),
            "expires_at": fields.Datetime.now() + timedelta(minutes=OTP_TTL_MINUTES),
        })
        return code

    def consume(self, email, code):
        """Valida el código. Devuelve el payload del postor o None."""
        otp = self.sudo().search(
            [("email", "=", email), ("expires_at", ">", fields.Datetime.now())],
            order="id desc", limit=1,
        )
        if not otp or otp.attempts >= OTP_MAX_ATTEMPTS:
            return None
        if otp.code_hash != self._hash_code(email, code):
            otp.attempts += 1
            return None
        payload = json.loads(otp.payload)
        otp.unlink()
        return payload

    def _cron_purge_expired(self):
        """Borra códigos vencidos: contienen RUT, correo y dirección del postor."""
        expired = self.sudo().search([("expires_at", "<=", fields.Datetime.now())])
        expired.unlink()
