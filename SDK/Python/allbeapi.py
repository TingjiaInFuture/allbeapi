import requests
import json

class AllBeApi:
    """
    AllBeAPI Python SDK - Minimal Utility Function Set
    Base URL: https://res.allbeapi.top

    Rapid development toolkit for prototyping and experimentation.
    Access ready-to-use functions without installing heavy dependencies.
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

    def parse(self, html, parser=None): # Changed html_content to html, added parser
        """Parses HTML content."""
        payload = {'html': html}
        if parser:
            payload['parser'] = parser
        return self.client._request('POST', '/beautifulsoup/parse', json_data=payload)

    def extract(self, html, selector, **kwargs): # Changed html_content to html
        """Extracts specific elements from HTML."""
        payload = {'html': html, 'selector': selector, **kwargs}
        return self.client._request('POST', '/beautifulsoup/extract', json_data=payload)

    def links(self, html, base_url=None, parser=None): # Changed html_content to html, added base_url and parser
        """Extracts all links from HTML."""
        payload = {'html': html}
        if base_url:
            payload['base_url'] = base_url
        if parser:
            payload['parser'] = parser
        return self.client._request('POST', '/beautifulsoup/links', json_data=payload)

    def images(self, html, base_url=None, parser=None): # Changed html_content to html, added base_url and parser
        """Extracts all images from HTML."""
        payload = {'html': html}
        if base_url:
            payload['base_url'] = base_url
        if parser:
            payload['parser'] = parser
        return self.client._request('POST', '/beautifulsoup/images', json_data=payload)

    def clean(self, html, remove_tags=None, keep_only=None, remove_comments=None, parser=None): # Changed html_content to html, added other params
        """Cleans HTML content."""
        payload = {'html': html}
        if remove_tags is not None:
            payload['remove_tags'] = remove_tags
        if keep_only is not None:
            payload['keep_only'] = keep_only
        if remove_comments is not None:
            payload['remove_comments'] = remove_comments
        if parser:
            payload['parser'] = parser
        return self.client._request('POST', '/beautifulsoup/clean', json_data=payload)

    def fetch(self, url, selector=None, parser=None): # Changed url_to_fetch to url, added selector and parser
        """Fetches a webpage and parses its content."""
        payload = {'url': url}
        if selector:
            payload['selector'] = selector
        if parser:
            payload['parser'] = parser
        return self.client._request('POST', '/beautifulsoup/fetch', json_data=payload)

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
        payload = {'html_content': html_content} # Changed 'html' to 'html_content'
        if options: payload['options'] = options
        return self.client._request('POST', '/sanitize-html/sanitize-html', json_data=payload)

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

    def lint(self, code, language='javascript', fix=False, **kwargs):
        """Lints JavaScript/TypeScript code using ESLint."""
        payload = {'code': code, 'language': language, 'fix': fix, **kwargs}
        # Removed redundant 'rules' parameter, pass rules directly in kwargs if needed by API
        return self.client._request('POST', '/eslint/lint', json_data=payload)

class DiffAPI:
    def __init__(self, client):
        self.client = client

    def compare(self, text1, text2, type='lines', outputFormat='json', **kwargs):
        """Compares two texts and returns the differences."""
        payload = {'text1': text1, 'text2': text2, 'type': type, 'outputFormat': outputFormat, **kwargs}
        return self.client._request('POST', '/diff/compare', json_data=payload)

class CsvParserAPI:
    def __init__(self, client):
        self.client = client

    def parse(self, csv_data, options=None, **kwargs):
        """Parses CSV data into JSON."""
        payload = {'csv_data': csv_data}
        if options is not None:  # Ensure options is only added if provided
            payload['options'] = options
        payload.update(kwargs) # Merge any additional kwargs
        return self.client._request('POST', '/csv-parser/parse', json_data=payload)

class MermaidCliAPI:
    def __init__(self, client):
        self.client = client

    def generate_diagram(self, definition, format='svg', **kwargs):
        """Generates a diagram from Mermaid text definition. Returns image bytes."""
        payload = {'definition': definition, 'format': format, **kwargs}
        # Initial request to generate the diagram and get the file path
        json_response = self.client._request('POST', '/mermaid-cli/generate-diagram', json_data=payload)
        
        if isinstance(json_response, dict) and 'filePath' in json_response:
            file_path = json_response['filePath']
            # Second request to fetch the actual diagram content
            # The _request method should handle returning bytes based on content type
            return self.client._request('GET', file_path) 
        else:
            # Handle cases where the expected filePath is not in the response
            raise Exception(f"Failed to retrieve diagram file path from MermaidCliAPI: {json_response}")

class PDFKitAPI:
    def __init__(self, client):
        self.client = client

    def generate(self, text_content, **kwargs):
        """Generates a PDF document using PDFKit. Returns PDF bytes."""
        payload = {'text_content': text_content, **kwargs}
        # Initial request to generate the PDF and get the file path
        json_response = self.client._request('POST', '/pdfkit/generate-pdf', json_data=payload)

        if isinstance(json_response, dict) and 'filePath' in json_response:
            file_path = json_response['filePath']
            # Second request to fetch the actual PDF content
            # The _request method should handle returning bytes based on content type
            return self.client._request('GET', file_path)
        else:
            # Handle cases where the expected filePath is not in the response
            raise Exception(f"Failed to retrieve PDF file path from PDFKitAPI: {json_response}")

class PillowAPI:
    def __init__(self, client):
        self.client = client

    def process(self, file_to_upload, operations, output_format='PNG', **kwargs):
        """
        Processes and edits images using Pillow. Returns image bytes.
        :param file_to_upload: Bytes of the image file.
        :param operations: List of operation strings (e.g., ["resize:200,200", "grayscale"]).
        :param output_format: Desired output format (e.g., 'PNG', 'JPEG').
        """
        if not isinstance(file_to_upload, bytes):
            raise ValueError("file_to_upload must be bytes.")
        
        files = {'file': ('image_file', file_to_upload)} 
        
        # API expects 'operations' as multiple form fields, not a single JSON string.
        # And other kwargs also as form fields.
        form_data = [('output_format', output_format)]
        for op in operations:
            form_data.append(('operations', op))
        
        for key, value in kwargs.items():
            form_data.append((key, str(value))) # Ensure all values are strings for form data

        # The _request method should handle 'data' being a list of tuples for multipart/form-data
        # when 'files' is also present. 'requests' library supports this.
        return self.client._request('POST', '/pillow/process-image', data=form_data, files=files)

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
