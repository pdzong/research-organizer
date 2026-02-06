import requests
from pdf2image import convert_from_path
import os


import requests
import os
import time
from pdf2image import convert_from_path

def pdf_to_markdown(pdf_path: str, server_url: str = "http://localhost:8080/v1/chat/completions") -> str:
    """
    Converts a local PDF to Markdown by processing it page-by-page via a local vLLM server.
    """
    
    # 1. Validation
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    print(f"📖 Loading PDF: {pdf_path}...")
    
    try:
        pages = convert_from_path(pdf_path, dpi=180)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF. Is Poppler installed and in PATH? Error: {e}")

    full_markdown = []
    total_pages = len(pages)
    print(f"📄 Found {total_pages} pages. Starting OCR processing...\n")

    # 3. Iterate through pages
    for i, page_image in enumerate(pages):
        page_num = i + 1
        
        # Create a temp filename for this page
        # We save it in the same folder as the script or PDF to ensure accessibility
        temp_filename = f"temp_ocr_page_{page_num}.jpg"
        abs_temp_path = os.path.abspath(temp_filename)
        
        # Save image locally
        page_image.save(abs_temp_path, "JPEG")

        # --- PATH TRANSLATION (Windows -> WSL) ---
        # The server (WSL) cannot read "C:\Users...", it needs "/mnt/c/Users..."
        # We assume the script is running on the C: drive.
        wsl_path = abs_temp_path.replace("C:", "/mnt/c").replace("\\", "/")
        file_url = f"file://{wsl_path}"

        prompt_text = (
            "Read this page carefully. Extract all content into a single Markdown format.\n"
            "1. Transcribe text exactly as it appears.\n"
            "2. Convert all mathematical formulas into LaTeX format (enclose in $$).\n"
            "3. Detect tables and convert them into Markdown tables.\n"
            "Do not summarize or skip any content."
        )

        # Prepare Request
        payload = {
            "model": "zai-org/GLM-OCR",
            "messages": [
                {
                    "role": "user",
                    "content": [                        
                        {"type": "image_url", "image_url": {"url": file_url}},
                        {"type": "text", "text": prompt_text}
                    ]
                }
            ],
            "temperature": 0.0, # Deterministic output
            "max_tokens": 4096  # Limit response size just in case
        }

        print(f"   ⏳ Processing Page {page_num}/{total_pages}...", end="\r")
        if i in (2, 3, 4, 8, 17):
            try:
                start_time = time.time()
                response = requests.post(server_url, json=payload)
                response.raise_for_status() # Raise error for bad HTTP codes
                
                # Extract content
                content = response.json()['choices'][0]['message']['content']
                
                # Add page delimiter for clarity
                page_text = f"\n\n\n\n{content}"
                full_markdown.append(page_text)
                
                duration = time.time() - start_time
                print(f"   ✅ Page {page_num}/{total_pages} done in {duration:.2f}s")

            except Exception as e:
                print(f"   ❌ Error on Page {page_num}: {e}")
                full_markdown.append(f"\n\n[ERROR PROCESSING PAGE {page_num}]\n\n")
            
            finally:
                print(f'the temp files stored {abs_temp_path}')
                # Cleanup temp file
                # if os.path.exists(abs_temp_path):
                #     os.remove(abs_temp_path)

    print("\n🎉 Conversion Complete!")
    return "".join(full_markdown)

# --- Usage Example ---
if __name__ == "__main__":
    # Your specific file path
    my_pdf = "C:\projects\\research_agent\\2601.19508v1.pdf"
    
    try:
        markdown_result = pdf_to_markdown(my_pdf)
        
        # Save the result to a file
        output_file = my_pdf.replace(".pdf", ".md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_result)
            
        print(f"💾 Saved Markdown to: {output_file}")
        
    except Exception as e:
        print(f"Fatal Error: {e}")

# # --- Configuration ---
# # 1. The path to your PDF inside WSL
# pdf_path = "C:/projects/research_agent/2602.04705v1.pdf"

# # 2. Where to save the temporary image (we'll put it next to the PDF)
# image_path = pdf_path.replace(".pdf", "_page13.jpg")

# wsl_image_path = f"/mnt/c/projects/research_agent/paper_images/2602.04705v1_p5.jpg"

# # 3. vLLM Server URL
# url = "http://localhost:8080/v1/chat/completions"

# # print(f"Processing: {pdf_path}...")

# # # --- Step 1: Convert PDF Page 1 to Image ---
# # try:
# #     # Convert first page only
# #     images = convert_from_path(pdf_path, first_page=13, last_page=20, dpi=150)
# #     for idx, img in enumerate(images):
# #         image_path = f"C:/projects/research_agent/paper_images/2602.04705v1_p{idx}.jpg"
# #         img.save(image_path, "JPEG")
# #     print(f"Saved temp image to: {image_path}")
# # except Exception as e:
# #     print(f"Error converting PDF: {e}")
# #     exit(1)

# payload = {
#     "model": "zai-org/GLM-OCR",
#     "messages": [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "Extract all text from this page into Markdown format."},
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         # NOTICE: We send the WSL path here!
#                         "url": f"file://{wsl_image_path}"
#                     }
#                 }
#             ]
#         }
#     ],
#     "temperature": 0.0, 
# }

# print(f"Sending request for: {wsl_image_path}")
# response = requests.post(url, json=payload)

# # --- Step 3: Output ---
# if response.status_code == 200:
#     print("\n--- OCR Result ---\n")
#     print(response.json()['choices'][0]['message']['content'])
# else:
#     print("Error:", response.text)


