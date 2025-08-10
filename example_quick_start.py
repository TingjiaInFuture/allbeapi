#!/usr/bin/env python3
"""
AllBeAPI Quick Start Example
Demonstrates practical usage for rapid prototyping
"""
import sys
import os

# Add SDK to path (in real usage, just ensure allbeapi.py is in your path)
repo_path = '/home/runner/work/allbeapi/allbeapi'
sys.path.insert(0, os.path.join(repo_path, 'SDK', 'Python'))

from allbeapi import AllBeApi

def main():
    print("🚀 AllBeAPI Quick Start Example")
    print("=" * 40)
    
    # Initialize client - only one line needed!
    api = AllBeApi()
    print("✓ SDK initialized - ready to use 13+ utility functions!")
    
    # Example 1: Rapid content processing
    print("\n📝 Example 1: Convert Markdown to HTML")
    markdown_content = """
# Rapid Prototype Demo
This is **AllBeAPI** in action:
- No dependencies to install
- Unified API calls
- Ready in 60 seconds
"""
    try:
        # Note: This would work if the API service was running
        print(f"Input: {markdown_content.strip()}")
        print("→ Would convert to HTML using api.marked.render()")
        print("✓ Perfect for blog engines, documentation, content management")
    except Exception as e:
        print(f"(Service not available: {e})")
    
    # Example 2: Quick image processing
    print("\n🖼️ Example 2: Image Processing")
    print("→ api.pillow.process(image_bytes, ['resize:300,300', 'convert:JPEG'])")
    print("✓ Perfect for user uploads, thumbnails, format conversion")
    
    # Example 3: Data validation
    print("\n✅ Example 3: JSON Schema Validation")
    print("→ api.ajv.validate(schema, data)")
    print("✓ Perfect for API validation, form processing")
    
    # Example 4: QR code generation
    print("\n📱 Example 4: QR Code Generation")
    print("→ qr_bytes = api.python_qrcode.generate_qrcode('https://example.com')")
    print("✓ Perfect for contact sharing, URL shortening, tickets")
    
    print("\n🎯 Use Cases:")
    print("• MVP development - get core features working fast")
    print("• Educational projects - focus on logic, not setup") 
    print("• Rapid experiments - test ideas quickly")
    print("• Prototype validation - build and iterate fast")
    
    print("\n🔧 Available Services:")
    services = [attr for attr in dir(api) 
                if not attr.startswith('_') and hasattr(getattr(api, attr), '__class__')]
    for i, service in enumerate(services, 1):
        print(f"{i:2d}. {service}")
    
    print(f"\n✨ {len(services)} utility functions ready to use!")
    print("📚 Full documentation: docs/api.html")

if __name__ == "__main__":
    main()