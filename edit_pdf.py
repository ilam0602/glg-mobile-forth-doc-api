#edit-pdf.py
import fitz  # PyMuPDF
import pytesseract
import io
from PIL import Image, ImageFilter, ImageEnhance, ExifTags

def correct_image_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # No EXIF data or no orientation data
        pass
    return img

def ocr_file(input_file_path, output_pdf_path):
    # Determine the file type from the extension
    if input_file_path.lower().endswith(('.pdf')):
        # Handle PDF input
        pdf_document = fitz.open(input_file_path)
        new_pdf = fitz.open()

        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            pix = page.get_pixmap()

            # Convert pixmap to PIL image
            img = Image.open(io.BytesIO(pix.tobytes()))

            # Correct image orientation
            img = correct_image_orientation(img)

            # Sharpen the image
            enhancer = ImageEnhance.Sharpness(img)
            sharpened_img = enhancer.enhance(2.0)  # Adjust factor as needed

            # Perform OCR on the sharpened image
            ocr_text = pytesseract.image_to_pdf_or_hocr(sharpened_img, extension='pdf')

            # Insert OCR results into the new PDF
            ocr_pdf_page = fitz.open("pdf", ocr_text)
            new_pdf.insert_pdf(ocr_pdf_page)
        
        # Save the new PDF to the output path
        new_pdf.save(output_pdf_path)
        new_pdf.close()
        pdf_document.close()

    elif input_file_path.lower().endswith(('.jpg', '.jpeg')):
        # Handle JPG input
        img = Image.open(input_file_path)

        # Correct image orientation
        img = correct_image_orientation(img)

        # Sharpen the image
        enhancer = ImageEnhance.Sharpness(img)
        sharpened_img = enhancer.enhance(2.0)  # Adjust factor as needed

        # Perform OCR on the sharpened image
        ocr_text = pytesseract.image_to_pdf_or_hocr(sharpened_img, extension='pdf')

        # Save the OCR result as a PDF
        with open(output_pdf_path, 'wb') as f:
            f.write(ocr_text)

    else:
        raise ValueError("Unsupported file format. Please provide a PDF or JPG file.")

def ocr_png_bytes(png_bytes):
    img = Image.open(io.BytesIO(png_bytes))
    
    # Correct image orientation
    img = correct_image_orientation(img)

    # Sharpen the image
    enhancer = ImageEnhance.Sharpness(img)
    sharpened_img = enhancer.enhance(2.0)

    # Perform OCR on the sharpened image and generate PDF bytes
    ocr_text = pytesseract.image_to_pdf_or_hocr(sharpened_img, extension='pdf')

    # Return the OCR result as a bytes object
    return ocr_text
