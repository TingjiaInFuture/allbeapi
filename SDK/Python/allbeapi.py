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

        self.marked = MarkedAPI(self)
        self.beautifulsoup = BeautifulSoupAPI(self)
        self.prettier = PrettierAPI(self)
        self.pygments = PygmentsAPI(self)
        self.python_qrcode = PythonQRCodeAPI(self) # python-qrcode
        self.sanitize_html = SanitizeHtmlAPI(self) # sanitize-html
        self.ajv = AjvAPI(self)
        self.eslint = ESLintAPI(self)
        self.diff = DiffAPI(self)
        self.csv_parser = CsvParserAPI(self) # csv-parser
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

class MarkedAPI:
    def __init__(self, client):
        self.client = client

    def render(self, markdown_text):
        """Converts Markdown text to HTML."""
        return self.client._request('POST', '/marked/render', json_data={'markdown': markdown_text})

class BeautifulSoupAPI:
    def __init__(self, client):
        self.client = client

    def parse(self, html_content):
        """Parses HTML content."""
        return self.client._request('POST', '/beautifulsoup/parse', json_data={'html': html_content})

    def extract(self, html_content, selector, **kwargs):
        """Extracts specific elements from HTML."""
        payload = {'html': html_content, 'selector': selector, **kwargs}
        return self.client._request('POST', '/beautifulsoup/extract', json_data=payload)

    def links(self, html_content):
        """Extracts all links from HTML."""
        return self.client._request('POST', '/beautifulsoup/links', json_data={'html': html_content})

    def images(self, html_content):
        """Extracts all images from HTML."""
        return self.client._request('POST', '/beautifulsoup/images', json_data={'html': html_content})

    def clean(self, html_content):
        """Cleans HTML content."""
        return self.client._request('POST', '/beautifulsoup/clean', json_data={'html': html_content})

    def fetch(self, url_to_fetch):
        """Fetches a webpage and parses its content."""
        return self.client._request('POST', '/beautifulsoup/fetch', json_data={'url': url_to_fetch})

    def health(self):
        """Health check for BeautifulSoup API."""
        return self.client._request('GET', '/beautifulsoup/health')

class PrettierAPI:
    def __init__(self, client):
        self.client = client

    def format(self, code, parser, options=None):
        """Formats code using Prettier."""
        payload = {'code': code, 'parser': parser}
        if options: payload['options'] = options
        return self.client._request('POST', '/prettier/format', json_data=payload)

    def check(self, code, parser, options=None):
        """Checks code formatting using Prettier."""
        payload = {'code': code, 'parser': parser}
        if options: payload['options'] = options
        return self.client._request('POST', '/prettier/check', json_data=payload)
    
    def batch(self, files, parser, options=None):
        """Batch format multiple code snippets."""
        # Assuming files is a list of dicts like [{ "name": "file.js", "code": "..." }]
        payload = {'files': files, 'parser': parser}
        if options: payload['options'] = options
        return self.client._request('POST', '/prettier/batch', json_data=payload)

    def get_parsers(self):
        """Gets available Prettier parsers."""
        return self.client._request('GET', '/prettier/parsers')

    def get_options(self):
        """Gets Prettier configuration options."""
        return self.client._request('GET', '/prettier/options')

    def health(self):
        """Health check for Prettier API."""
        return self.client._request('GET', '/prettier/health')

    def get_info(self):
        """Get Prettier API information."""
        return self.client._request('GET', '/prettier/info')

class PygmentsAPI:
    def __init__(self, client):
        self.client = client

    def highlight(self, code, language, **kwargs):
        """Highlights code syntax using Pygments."""
        payload = {'code': code, 'language': language, **kwargs}
        return self.client._request('POST', '/pygments/highlight', json_data=payload)

class PythonQRCodeAPI:
    def __init__(self, client):
        self.client = client

    def generate_qrcode(self, data, **kwargs):
        """Generates a QR code image. Returns image bytes."""
        payload = {'data': data, **kwargs}
        return self.client._request('POST', '/python-qrcode/generate-qrcode', json_data=payload)

class SanitizeHtmlAPI:
    def __init__(self, client):
        self.client = client

    def sanitize(self, html_content, options=None):
        """Sanitizes HTML content to prevent XSS attacks."""
        payload = {'html': html_content}
        if options: payload['options'] = options
        return self.client._request('POST', '/sanitize-html', json_data=payload)

class AjvAPI:
    def __init__(self, client):
        self.client = client

    def validate(self, schema, data_to_validate):
        """Validates JSON data against a schema using Ajv."""
        payload = {'schema': schema, 'data': data_to_validate}
        return self.client._request('POST', '/ajv/validate', json_data=payload)

class ESLintAPI:
    def __init__(self, client):
        self.client = client

    def lint(self, code, rules=None, **kwargs):
        """Lints JavaScript/TypeScript code using ESLint."""
        payload = {'code': code, **kwargs}
        if rules: payload['rules'] = rules
        return self.client._request('POST', '/eslint/lint', json_data=payload)

class DiffAPI:
    def __init__(self, client):
        self.client = client

    def compare(self, text1, text2, **kwargs):
        """Compares two texts and returns the differences."""
        payload = {'text1': text1, 'text2': text2, **kwargs}
        return self.client._request('POST', '/diff/compare', json_data=payload)

class CsvParserAPI:
    def __init__(self, client):
        self.client = client

    def parse(self, csv_data, **kwargs):
        """Parses CSV data into JSON."""
        # The API expects 'csv_data' as the key for the CSV content
        payload = {'csv_data': csv_data, **kwargs}
        return self.client._request('POST', '/csv-parser/parse', json_data=payload)

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

if __name__ == '__main__':
    # Example Usage (Illustrative - requires running AllBeApi services)
    # client = AllBeApi()

    # try:
        # Markdown to HTML
        # html_output = client.marked.render("# Hello Python SDK")
        # print("Marked Output:", html_output)

        # # QR Code Generation (returns bytes)
        # qr_image_bytes = client.python_qrcode.generate_qrcode("https://res.allbeapi.top")
        # with open("example_qrcode.png", "wb") as f:
        #     f.write(qr_image_bytes)
        # print("QR Code saved to example_qrcode.png")

        # # Prettier format (example)
        # formatted_code = client.prettier.format("const foo =    1", "babel")
        # print("Prettier Output:", formatted_code)

        # # BeautifulSoup parse (example)
        # parsed_html = client.beautifulsoup.parse("<html><body><h1>Hi</h1></body></html>")
        # print("BeautifulSoup Parsed:", parsed_html)
        
        # # Pillow API (example with URL)
        # # Note: This is a placeholder URL and operation. The actual API might require specific image URLs and operations.
        # # processed_image_bytes = client.pillow.process(image_url_or_data="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png", operation="resize", width=100, height=50)
        # # with open("processed_image.png", "wb") as f:
        # #     f.write(processed_image_bytes)
        # # print("Processed image saved to processed_image.png")

    # except requests.exceptions.HTTPError as e:
    #     print(f"API Error: {e.response.status_code} - {e.response.text}")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")
    pass
