from odoo import http
import requests
import json
import time
import hashlib
import hmac
import base64

class HairStyleIntegration(http.Controller):

    def generate_id_token(self, client_id, client_secret, timestamp):
        """
        Genera un ID token para la autenticación con la API de YouCam Online Editor.
        """
        # Crear el string base para el token
        base_string = f"{client_id}&{timestamp}"

        # Generar la firma HMAC usando el client_secret
        signature = hmac.new(
            client_secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Codificar la firma en base64
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        # Concatenar el client_id, timestamp y la firma para obtener el token
        id_token = f"{client_id}.{timestamp}.{encoded_signature}"

        return id_token

    @http.route('/hair_style/apply', type='http', auth='public', methods=['POST'], csrf=False)
    def apply_hair_style(self, **kwargs):
        # Obtener datos del formulario
        image = kwargs.get('image')
        style = kwargs.get('style')

        # Autenticación con la API de YouCam Online Editor
        client_id = 'TU_CLIENT_ID'
        client_secret = 'TU_CLIENT_SECRET'
        timestamp = str(int(time.time() * 1000))
        id_token = self.generate_id_token(client_id, client_secret, timestamp)

        auth_response = requests.post(
            'https://yce-api-01.perfectcorp.com/s2s/v1.0/client/auth',
            json={
                'client_id': client_id,
                'id_token': id_token
            }
        )

        if auth_response.status_code == 200:
            access_token = auth_response.json().get('result').get('access_token')

            # Subir la imagen a la API
            upload_response = requests.post(
                'https://yce-api-01.perfectcorp.com/s2s/v1.0/file/hair-style',
                headers={
                    'Authorization': f'Bearer {access_token}'
                },
                files={'file': image}
            )

            if upload_response.status_code == 200:
                file_id = upload_response.json().get('result').get('file_id')

                # Aplicar el estilo de cabello
                task_response = requests.post(
                    'https://yce-api-01.perfectcorp.com/s2s/v1.0/task/hair-style',
                    headers={
                        'Authorization': f'Bearer {access_token}'
                    },
                    json={
                        'file_id': file_id,
                        'style': style
                    }
                )

                if task_response.status_code == 200:
                    task_id = task_response.json().get('result').get('task_id')

                    # Consultar el estado de la tarea
                    while True:
                        status_response = requests.get(
                            f'https://yce-api-01.perfectcorp.com/s2s/v1.0/task/hair-style/{task_id}',
                            headers={
                                'Authorization': f'Bearer {access_token}'
                            }
                        )

                        if status_response.status_code == 200:
                            status = status_response.json().get('result').get('status')
                            if status == 'success':
                                result_url = status_response.json().get('result').get('result_url')
                                return http.request.render('website_hair_style_integration.result_template', {
                                    'image_url': result_url
                                })
                            elif status == 'error':
                                return "Error al procesar la imagen."
                        time.sleep(2)
            return "Error al subir la imagen."
        return "Error de autenticación con la API."

