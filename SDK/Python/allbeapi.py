import requests
import json

class AllBeApi:
    """
    AllBeAPI Python SDK
    Base URL: https://res.allbeapi.top

    This SDK provides a convenient way to interact with the AllBeAPI services.
    It includes a main client class `AllBeApi` and specific classes for each API service.
    """
    def __init__(self, base_url='https://res.allbeapi.top'):
        """
        Initializes a new instance of the AllBeApi client.
        :param base_url: The base URL for the API.
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

        self.eslint = ESLintAPI(self)
        self.mermaid_cli = MermaidCliAPI(self) # mermaid-cli
        self.pdfkit = PDFKitAPI(self)
        self.pillow = PillowAPI(self)

    def _request(self, method, path, params=None, data=None, json_data=None, files=None):
        """
        Internal method to make requests to the API.
        :param method: The HTTP method (e.g., 'GET', 'POST').
        :param path: The API endpoint path.
        :param params: Query parameters for GET requests.
        :param data: Form data for POST requests.
        :param json_data: JSON body for POST/PUT requests.
        :param files: Files for multipart/form-data uploads.
        :return: The response from the API (parsed JSON or raw content).
        :raises: requests.exceptions.HTTPError for bad responses (4xx or 5xx).
        """
        url = f'{self.base_url}{path}'
        headers = self.session.headers.copy()

        if json_data and files:
            raise ValueError("Cannot provide both json_data and files.")
        
        if files:
            # For multipart/form-data, let requests set the Content-Type
            if 'Content-Type' in headers:
                del headers['Content-Type']
        elif not data and not json_data:
             # For GET or POST with no body, ensure Content-Type is not set if not needed
            if method.upper() == 'GET' and 'Content-Type' in headers:
                 del headers['Content-Type']
            elif method.upper() == 'POST' and not data and not json_data and 'Content-Type' in headers:
                 # Keep Content-Type if it was explicitly set for an empty POST body, otherwise remove
                 pass # Or consider removing if it's the default application/json

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                files=files,
                headers=headers
            )
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            # For image, pdf, or other binary types, return raw content
            elif any(ct in content_type for ct in ['image', 'application/pdf']):
                return response.content
            return response.text # Fallback for other text-based types
        except requests.exceptions.RequestException as e:
            # Log or handle more specific exceptions as needed
            print(f"Request to {method} {url} failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise


class ESLintAPI:
    def __init__(self, client):
        self.client = client

    def lint(self, code, rules=None, **kwargs):
        """Lints JavaScript/TypeScript code using ESLint."""
        payload = {'code': code, **kwargs}
        if rules: payload['rules'] = rules
        return self.client._request('POST', '/eslint/lint', json_data=payload)



class ESLintAPI:
    def __init__(self, client):
        self.client = client

    def lint(self, code, rules=None, **kwargs):
        """Lints JavaScript/TypeScript code using ESLint."""
        payload = {'code': code, **kwargs}
        if rules: payload['rules'] = rules
        return self.client._request('POST', '/eslint/lint', json_data=payload)

class MermaidCliAPI:
    def __init__(self, client):
        self.client = client

    def generate_diagram(self, mermaid_definition, **kwargs):
        """Generates a diagram from Mermaid text definition. Returns image bytes."""
        payload = {'mermaid': mermaid_definition, **kwargs}
        return self.client._request('POST', '/mermaid-cli/generate-diagram', json_data=payload)

class PDFKitAPI:
    def __init__(self, client):
        self.client = client

    def generate(self, content, **kwargs):
        """Generates a PDF document using PDFKit. Returns PDF bytes."""
        payload = {'content': content, **kwargs}
        return self.client._request('POST', '/pdfkit/generate', json_data=payload)

class PillowAPI:
    def __init__(self, client):
        self.client = client

    def process(self, image_url_or_data, operation, files=None, **kwargs):
        """
        Processes and edits images using Pillow. Returns image bytes.
        Can accept image_url (string) or image_data (bytes) via files argument.
        """
        payload = {'operation': operation, **kwargs}
        
        # The API documentation implies image_url is a primary way, but for local files or direct data,
        # sending as multipart/form-data might be necessary if the API supports it.
        # The current API spec in api-index.json for /pillow/process is POST, implying JSON body.
        # If it needs to handle file uploads, the server-side and this SDK client would need adjustment.
        # For now, assuming image_url is part of the JSON payload as per typical API design for URLs.
        # If `image_url_or_data` is bytes, it should be sent via `files` and `payload` should not contain `image_url`.
        
        if isinstance(image_url_or_data, str):
            payload['image_url'] = image_url_or_data
            return self.client._request('POST', '/pillow/process', json_data=payload)
        elif isinstance(image_url_or_data, bytes) and files:
            # This branch assumes the API can take 'operation' and other kwargs as form fields
            # alongside the file. This is a common pattern but not explicitly in api-index.json.
            # `files` should be in the format {'image_file_name': image_data_bytes}
            # `data` (form fields) would be `payload`
            return self.client._request('POST', '/pillow/process', data=payload, files=files)
        elif isinstance(image_url_or_data, bytes) and not files:
             raise ValueError("image_data (bytes) provided to PillowAPI.process without `files` argument. Please provide files={'image': image_data_bytes}")
        else:
            raise ValueError("Invalid image_url_or_data type. Must be str (URL) or bytes (with files argument).")


