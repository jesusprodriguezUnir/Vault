
import sys
import os

# Check imports before anything else
try:
    import markdown
    from xhtml2pdf import pisa
except ImportError as e:
    print("Error: Missing required libraries.")
    print(f"Details: {e}")
    print("\nPlease install the requirements running:")
    print("pip install markdown xhtml2pdf")
    sys.exit(1)

def convert_md_to_pdf(source_md, output_pdf):
    # 1. Read Markdown file
    if not os.path.exists(source_md):
        print(f"Error: Source file '{source_md}' not found.")
        return

    with open(source_md, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 2. Convert Markdown to HTML
    # We use 'extra' extension for tables and other features if needed
    html_body = markdown.markdown(md_text, extensions=['extra'])

    # 3. Add some basic styling for the PDF
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, sans-serif; font-size: 12pt; line-height: 1.5; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; margin-top: 30px; }}
            h2 {{ color: #34495e; margin-top: 25px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            h3 {{ color: #16a085; margin-top: 20px; }}
            code {{ background-color: #f8f8f8; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; border: 1px solid #e1e1e1; }}
            blockquote {{ border-left: 4px solid #e74c3c; padding-left: 15px; background-color: #f9f9f9; color: #555; }}
            a {{ color: #2980b9; text-decoration: none; }}
            ul {{ margin-bottom: 15px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_body}
        </div>
    </body>
    </html>
    """

    # 4. Generate PDF
    with open(output_pdf, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

    if pisa_status.err:
        print(f"Error generating PDF: {pisa_status.err}")
    else:
        print(f"Success! PDF created at: {output_pdf}")

if __name__ == "__main__":
    # Define paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MD_FILE = os.path.join(BASE_DIR, "MANUAL_USUARIO.md")
    PDF_FILE = os.path.join(BASE_DIR, "MANUAL_USUARIO.pdf")

    print(f"Converting '{MD_FILE}' to PDF...")
    convert_md_to_pdf(MD_FILE, PDF_FILE)
