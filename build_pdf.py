import markdown
import sys
import re

def convert_md_to_html(md_path, html_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Process mermaid blocks to simple pre/code blocks or ignore them, as headless Edge won't render mermaid JS easily without waiting.
    md_text = re.sub(r'```mermaid(.*?)```', r'<div class="mermaid-placeholder"><i>[Mermaid diagram - viz zdrojový kód]</i></div>', md_text, flags=re.DOTALL)
    
    # Process github alerts
    md_text = md_text.replace('> [!NOTE]', '<div class="alert alert-note"><strong>Poznámka:</strong><br/>')
    md_text = md_text.replace('> [!WARNING]', '<div class="alert alert-warning"><strong>Upozornění:</strong><br/>')
    md_text = md_text.replace('> [!CAUTION]', '<div class="alert alert-caution"><strong>Varování:</strong><br/>')
    md_text = md_text.replace('> [!IMPORTANT]', '<div class="alert alert-important"><strong>Důležité:</strong><br/>')
    md_text = re.sub(r'(<div class="alert[^>]+>.*?)(?=\n\n|\Z)', r'\1</div>', md_text, flags=re.DOTALL) # Basic closure

    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <title>Sémantický index dokumentů</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
                @bottom-center {{
                    content: counter(page);
                }}
            }}
            body {{
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
                color: #2D3748;
                max-width: 100%;
                margin: 0;
                padding: 0;
            }}
            h1 {{
                color: #1A202C;
                font-size: 28px;
                border-bottom: 2px solid #E2E8F0;
                padding-bottom: 10px;
                margin-top: 40px;
            }}
            h1:first-child {{
                margin-top: 0;
                font-size: 36px;
                color: #2B6CB0;
                text-align: center;
                border-bottom: none;
                margin-bottom: 50px;
            }}
            h2 {{
                color: #2B6CB0;
                font-size: 22px;
                margin-top: 30px;
                border-bottom: 1px solid #E2E8F0;
                padding-bottom: 5px;
            }}
            h3 {{
                color: #4A5568;
                font-size: 18px;
                margin-top: 25px;
            }}
            p, li {{
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 13px;
            }}
            th, td {{
                border: 1px solid #CBD5E0;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #EDF2F7;
                color: #2D3748;
                font-weight: 600;
            }}
            tr:nth-child(even) {{
                background-color: #F7FAFC;
            }}
            code {{
                background-color: #EDF2F7;
                padding: 2px 4px;
                border-radius: 4px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 13px;
                color: #E53E3E;
            }}
            pre code {{
                display: block;
                padding: 15px;
                background-color: #1A202C;
                color: #A0AEC0;
                border-radius: 8px;
                overflow-x: auto;
            }}
            .alert {{
                padding: 15px;
                border-left: 5px solid;
                margin: 20px 0;
                border-radius: 0 4px 4px 0;
                font-size: 14px;
            }}
            .alert-note {{
                background-color: #EBF8FF;
                border-left-color: #3182CE;
                color: #2B6CB0;
            }}
            .alert-warning {{
                background-color: #FFFFF0;
                border-left-color: #D69E2E;
                color: #B7791F;
            }}
            .mermaid-placeholder {{
                padding: 20px;
                background-color: #EDF2F7;
                border: 1px dashed #CBD5E0;
                text-align: center;
                margin: 20px 0;
                border-radius: 8px;
            }}
            hr {{
                border: 0;
                height: 1px;
                background: #E2E8F0;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    convert_md_to_html("analyza_a_plan.md", "analyza.html")
    print("HTML generated successfully.")
