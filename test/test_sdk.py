import unittest
import os
from allbeapi import AllBeApi
import requests

class TestAllBeApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = AllBeApi()
        # Create a dummy image file for pillow upload test
        cls.dummy_image_path = "dummy_image.png"
        with open(cls.dummy_image_path, "wb") as f:
            # A minimal valid PNG (1x1 transparent pixel)
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2\x1e\x78\xa1\x00\x00\x00\x00IEND\xaeB`\x82')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.dummy_image_path):
            os.remove(cls.dummy_image_path)

    def test_marked_render(self):
        print("\nTesting MarkedAPI render...")
        response = self.client.marked.render("# Hello Markdown")
        self.assertIn("<h1>Hello Markdown</h1>", response)
        print("MarkedAPI render test passed.")

    def test_beautifulsoup_api(self):
        print("\nTesting BeautifulSoupAPI...")
        html_content = "<html><head><title>Test Page</title></head><body><h1>Hello</h1><a href=\'page.html\'>Link</a><img src=\'img.png\'></body></html>"
        
        print("Testing BeautifulSoupAPI parse...")
        response_parse = self.client.beautifulsoup.parse(html_content)
        self.assertIsNotNone(response_parse) # Basic check, structure depends on server
        print("BeautifulSoupAPI parse test passed.")

        print("Testing BeautifulSoupAPI extract...")
        response_extract = self.client.beautifulsoup.extract(html_content, "h1")
        self.assertIsNotNone(response_extract)
        print("BeautifulSoupAPI extract test passed.")

        print("Testing BeautifulSoupAPI links...")
        response_links = self.client.beautifulsoup.links(html_content)
        self.assertIsInstance(response_links, list)
        print("BeautifulSoupAPI links test passed.")

        print("Testing BeautifulSoupAPI images...")
        response_images = self.client.beautifulsoup.images(html_content)
        self.assertIsInstance(response_images, list)
        print("BeautifulSoupAPI images test passed.")

        print("Testing BeautifulSoupAPI clean...")
        response_clean = self.client.beautifulsoup.clean(html_content)
        self.assertIsNotNone(response_clean)
        print("BeautifulSoupAPI clean test passed.")
        
        # Skipping fetch to avoid external dependency in automated test if not needed
        # print("Testing BeautifulSoupAPI fetch...")
        # try:
        #     response_fetch = self.client.beautifulsoup.fetch("https://example.com") # Replace with a reliable URL
        #     self.assertIsNotNone(response_fetch)
        # except requests.exceptions.RequestException as e:
        #     print(f"Skipping BeautifulSoup fetch test due to network issue: {e}")
        # print("BeautifulSoupAPI fetch test passed or skipped.")


        print("Testing BeautifulSoupAPI health...")
        response_health = self.client.beautifulsoup.health()
        self.assertIsNotNone(response_health) # Adjust based on expected health response
        print("BeautifulSoupAPI health test passed.")


    def test_prettier_api(self):
        print("\nTesting PrettierAPI...")
        code_to_format = "const foo =    1"
        
        print("Testing PrettierAPI format...")
        response_format = self.client.prettier.format(code_to_format, "babel")
        self.assertIn("const foo = 1;", response_format.get("formattedCode", ""))
        print("PrettierAPI format test passed.")

        print("Testing PrettierAPI check...")
        response_check = self.client.prettier.check(code_to_format, "babel")
        self.assertIsInstance(response_check, dict) # or bool, depending on API
        print("PrettierAPI check test passed.")

        print("Testing PrettierAPI batch...")
        files_to_format = [{"name": "test.js", "code": "let   a =  1"}]
        response_batch = self.client.prettier.batch(files_to_format, "babel")
        self.assertIsInstance(response_batch, list)
        if response_batch:
            self.assertIn("let a = 1;", response_batch[0].get("formattedCode", ""))
        print("PrettierAPI batch test passed.")

        print("Testing PrettierAPI get_parsers...")
        response_parsers = self.client.prettier.get_parsers()
        self.assertIsInstance(response_parsers, list)
        print("PrettierAPI get_parsers test passed.")

        print("Testing PrettierAPI get_options...")
        response_options = self.client.prettier.get_options()
        self.assertIsInstance(response_options, dict)
        print("PrettierAPI get_options test passed.")
        
        print("Testing PrettierAPI health...")
        response_health = self.client.prettier.health()
        self.assertIsNotNone(response_health)
        print("PrettierAPI health test passed.")

        print("Testing PrettierAPI get_info...")
        response_info = self.client.prettier.get_info()
        self.assertIsInstance(response_info, dict)
        print("PrettierAPI get_info test passed.")


    def test_pygments_highlight(self):
        print("\nTesting PygmentsAPI highlight...")
        response = self.client.pygments.highlight("print('Hello')", "python")
        self.assertIn("<span", response) # Expecting HTML output
        print("PygmentsAPI highlight test passed.")

    def test_python_qrcode_generate(self):
        print("\nTesting PythonQRCodeAPI generate_qrcode...")
        response = self.client.python_qrcode.generate_qrcode("test data")
        self.assertIsInstance(response, bytes)
        print("PythonQRCodeAPI generate_qrcode test passed.")

    def test_sanitize_html_sanitize(self):
        print("\nTesting SanitizeHtmlAPI sanitize...")
        response = self.client.sanitize_html.sanitize("<script>alert('xss')</script><b>safe</b>")
        self.assertNotIn("<script>", response)
        self.assertIn("<b>safe</b>", response)
        print("SanitizeHtmlAPI sanitize test passed.")

    def test_ajv_validate(self):
        print("\nTesting AjvAPI validate...")
        schema = {"type": "object", "properties": {"foo": {"type": "integer"}}, "required": ["foo"]}
        data_valid = {"foo": 1}
        data_invalid = {"foo": "bar"}
        
        response_valid = self.client.ajv.validate(schema, data_valid)
        self.assertTrue(response_valid.get("valid", False))
        
        response_invalid = self.client.ajv.validate(schema, data_invalid)
        self.assertFalse(response_invalid.get("valid", True))
        print("AjvAPI validate test passed.")

    def test_eslint_lint(self):
        print("\nTesting ESLintAPI lint...")
        # ESLint might require specific setup or have more complex responses
        response = self.client.eslint.lint("var foo = 1") # Simple JS
        self.assertIsInstance(response, list) # Expecting a list of linting issues
        print("ESLintAPI lint test passed.")

    def test_diff_compare(self):
        print("\nTesting DiffAPI compare...")
        response = self.client.diff.compare("text one", "text two")
        self.assertIsInstance(response, list) # Or dict, depending on API's diff format
        print("DiffAPI compare test passed.")

    def test_csv_parser_parse(self):
        print("\nTesting CsvParserAPI parse...")
        csv_data = "header1,header2\nvalue1,value2"
        response = self.client.csv_parser.parse(csv_data)
        self.assertIsInstance(response, list)
        if response:
            self.assertEqual(response[0].get("header1"), "value1")
        print("CsvParserAPI parse test passed.")

    def test_mermaid_cli_generate_diagram(self):
        print("\nTesting MermaidCliAPI generate_diagram...")
        mermaid_def = "graph TD; A-->B;"
        response = self.client.mermaid_cli.generate_diagram(mermaid_def)
        self.assertIsInstance(response, bytes) # Expecting image bytes (e.g., SVG or PNG)
        print("MermaidCliAPI generate_diagram test passed.")

    def test_pdfkit_generate(self):
        print("\nTesting PDFKitAPI generate...")
        html_content = "<h1>Hello PDF</h1>"
        response = self.client.pdfkit.generate(html_content)
        self.assertIsInstance(response, bytes)
        print("PDFKitAPI generate test passed.")

    def test_pillow_process_url(self):
        print("\nTesting PillowAPI process with URL...")
        # This test uses a public placeholder image.
        # The AllBeApi Pillow service must be able to fetch this URL.
        # Replace with a more stable or self-hosted image if needed.
        # Note: Operations and their params depend on the Pillow API's capabilities.
        # This is a basic test assuming a 'resize' operation exists.
        image_url = "https://via.placeholder.com/150" # A common placeholder service
        try:
            response = self.client.pillow.process(image_url_or_data=image_url, operation="resize", width=50, height=50)
            self.assertIsInstance(response, bytes)
            print("PillowAPI process with URL test passed.")
        except requests.exceptions.RequestException as e:
            print(f"Skipping PillowAPI process with URL test due to network/server issue: {e}")
        except Exception as e:
            print(f"PillowAPI process with URL test failed: {e}")
            self.fail(f"PillowAPI process with URL failed: {e}")
            
    def test_pillow_process_bytes(self):
        print("\nTesting PillowAPI process with bytes...")
        try:
            with open(self.dummy_image_path, "rb") as f:
                image_bytes = f.read()
            
            # The 'files' argument should be a dictionary like {'file_form_name': (filename, file_bytes, content_type)}
            # The server-side API for Pillow needs to be designed to accept 'image' (or similar) as a file part
            # and 'operation', 'width', 'height' as form data fields.
            # The current SDK's _request method might need adjustment if it sends 'data' as JSON when 'files' is present.
            # For now, assuming the SDK's _request handles this by sending 'data' as form fields.
            files = {'image': (self.dummy_image_path, image_bytes, 'image/png')}
            response = self.client.pillow.process(image_url_or_data=image_bytes, operation="resize", files=files, width=1, height=1) # width/height for the dummy
            self.assertIsInstance(response, bytes)
            print("PillowAPI process with bytes test passed.")
        except FileNotFoundError:
            print(f"Skipping PillowAPI process with bytes test: dummy image not found at {self.dummy_image_path}")
        except Exception as e:
            # This can fail if the server doesn't expect multipart for /pillow/process or if params aren't passed correctly
            print(f"PillowAPI process with bytes test failed: {e}")
            # Check if response has more details if it's an HTTPError
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            self.fail(f"PillowAPI process with bytes failed: {e}")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# Example of how to run if you want to see output directly in some environments
# suite = unittest.TestSuite()
# suite.addTest(unittest.makeSuite(TestAllBeApi))
# runner = unittest.TextTestRunner()
# runner.run(suite)