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
        Generates an ID token for authentication with the YouCam Online Editor API.
        """
        # Create the base string for the token
        base_string = f"{client_id}&{timestamp}"

        # Generate the HMAC signature using the client_secret
        signature = hmac.new(
            client_secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Encode the signature in base64
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        # Concatenate the client_id, timestamp, and signature to obtain the token
        id_token = f"{client_id}.{timestamp}.{encoded_signature}"

        return id_token

    @http.route('/hair_style/apply', type='http', auth='public', methods=['POST'], csrf=False)
    def apply_hair_style(self, **kwargs):
        # Obtain form data
        image = http.request.httprequest.files.get('image')  # Get the uploaded file
        style = kwargs.get('style')  # Get the selected hairstyle

        if not image or not style:
            return "Error: Both image and style must be provided."

        # Client ID and Client Secret (Add your actual credentials here)
        client_id = 'HczjFjWQ5063U0V6nUFVuArd7OLJDa5D'  # Replace with your Client ID
        client_secret = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCH/whjFmMH7KpRWSIQxcM9qweVhLx3YNLByGC+TTBuzHdNeDl+u2euECoHS9OEaFQ5I+Ze7jdXLpJiydSLu3GJnmyeZV4yOKlkknRWgZ8VYZv8U634s95fVLUnXie6WiHmYJvrUyQfZ+jpY5vCCnHm6fAVPtJ4vcHCsSPUjVioxQIDAQAB'  # Replace with your Client Secret

        # Generate the ID token
        timestamp = str(int(time.time() * 1000))
        id_token = self.generate_id_token(client_id, client_secret, timestamp)

        # Authenticate with the API
        auth_response = requests.post(
            'https://yce-api-01.perfectcorp.com/s2s/v1.0/client/auth',
            json={
                'client_id': client_id,
                'id_token': id_token
            }
        )

        if auth_response.status_code == 200:
            access_token = auth_response.json().get('result', {}).get('access_token')

            # Upload the image to the API
            upload_response = requests.post(
                'https://yce-api-01.perfectcorp.com/s2s/v1.0/file/hair-style',
                headers={
                    'Authorization': f'Bearer {access_token}'
                },
                files={'file': image}
            )

            if upload_response.status_code == 200:
                file_id = upload_response.json().get('result', {}).get('file_id')

                # Apply the hairstyle
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
                    task_id = task_response.json().get('result', {}).get('task_id')

                    # Poll the API for task completion
                    while True:
                        status_response = requests.get(
                            f'https://yce-api-01.perfectcorp.com/s2s/v1.0/task/hair-style/{task_id}',
                            headers={
                                'Authorization': f'Bearer {access_token}'
                            }
                        )

                        if status_response.status_code == 200:
                            status = status_response.json().get('result', {}).get('status')
                            if status == 'success':
                                result_url = status_response.json().get('result', {}).get('result_url')
                                return http.request.render('website_hair_style.result_template', {
                                    'image_url': result_url
                                })
                            elif status == 'error':
                                return "Error: The image could not be processed."
                        time.sleep(2)  # Wait before retrying

            return "Error: The image could not be uploaded."
        return "Error: Authentication with the API failed."
