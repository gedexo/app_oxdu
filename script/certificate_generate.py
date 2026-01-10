from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import openpyxl
import os


# Paths (adjust as needed)
CERTIFICATE_IMAGE = "/home/gedexo/Gedexo/oxdu_erp/oxdu_erp/static/app/assets/images/certificate_template.jpg"
EXCEL_FILE = "/home/gedexo/Gedexo/oxdu_erp/oxdu_erp/static/app/assets/exel/latest.xlsx"
OUTPUT_FOLDER = "/home/gedexo/Gedexo/oxdu_erp/oxdu_erp/static/app/assets/certificates"
FONT_PATH_BOLD = "/home/gedexo/Gedexo/oxdu_erp/oxdu_erp/static/app/assets/font/Poppins/Poppins-Bold.ttf"
FONT_PATH_REGULAR = "/home/gedexo/Gedexo/oxdu_erp/oxdu_erp/static/app/assets/font/Poppins/Poppins-Regular.ttf"

FONT_SIZE_LARGE = 45  # For Issue Date, ID Number
FONT_SIZE_BODY_TEXT = 50  # For the paragraph body text
TEXT_COLOR = (0, 0, 0)

# Coordinates for individual fields
FIELD_POSITIONS = {
    "Issue Date": (600, 1503),
    "ID Number": (2060, 1500),
}

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def format_date_long(date_value):
    if isinstance(date_value, datetime):
        return date_value.strftime("%B %-d %Y")
    try:
        parsed = datetime.strptime(str(date_value), "%Y-%m-%d")
    except ValueError:
        try:
            parsed = datetime.strptime(str(date_value), "%d/%m/%Y")
        except ValueError:
            return str(date_value)
    return parsed.strftime("%B %-d %Y")

def format_date_dmy(date_value):
    if isinstance(date_value, datetime):
        return date_value.strftime("%-d/%-m/%Y")
    try:
        parsed = datetime.strptime(str(date_value), "%Y-%m-%d")
    except ValueError:
        try:
            parsed = datetime.strptime(str(date_value), "%d/%m/%Y")
        except ValueError:
            return str(date_value)
    return parsed.strftime("%-d/%-m/%Y")


def draw_text_with_letter_spacing(draw_obj, position, text, font, fill, letter_spacing):
    """Draw text with letter spacing applied."""
    x, y = position
    for i, char in enumerate(text):
        draw_obj.text((x, y), char, font=font, fill=fill)
        char_width = font.getbbox(char)[2] - font.getbbox(char)[0]
        x += char_width + letter_spacing
    return x

def draw_multiline_text_with_bold(draw_obj, full_text, bold_parts, position, font_regular, font_bold, fill, max_width=1500, line_spacing=0, first_line_indent=0):
    """
    Draws justified multiline text with specific bold replacements and optional first-line indentation.
    """
    x, y = position
    space_width = font_regular.getbbox(" ")[2] - font_regular.getbbox(" ")[0]
    line_height = (font_regular.getbbox("A")[3] - font_regular.getbbox("A")[1]) + line_spacing

    words = full_text.split()
    lines = []
    current_line = []
    current_width = 0
    is_first_line = True

    def text_width(text, font):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    i = 0
    while i < len(words):
        word = words[i]
        matched_bold = None
        matched_text = None

        for key, replacement in bold_parts.items():
            key_words = key.split()
            if words[i:i+len(key_words)] == key_words:
                matched_bold = replacement
                matched_text = key_words
                break

        if matched_bold:
            w = text_width(matched_bold, font_bold)
            if current_width + w <= max_width:
                current_line.append((matched_bold, font_bold))
                current_width += w + space_width
                i += len(matched_text)
            else:
                lines.append(current_line)
                current_line = []
                current_width = 0
        else:
            w = text_width(word, font_regular)
            if current_width + w <= max_width:
                current_line.append((word, font_regular))
                current_width += w + space_width
                i += 1
            else:
                lines.append(current_line)
                current_line = []
                current_width = 0
    if current_line:
        lines.append(current_line)

    # Draw justified lines
    for line_num, line in enumerate(lines):
        if line_num == 0:
            line_x = x + first_line_indent
        else:
            line_x = x

        # Last line is left-aligned, not justified
        if line_num == len(lines) - 1 or len(line) == 1:
            for txt, fnt in line:
                draw_obj.text((line_x, y), txt, font=fnt, fill=fill)
                line_x += text_width(txt, fnt) + space_width
        else:
            total_text_width = sum(text_width(txt, fnt) for txt, fnt in line)
            spaces_needed = len(line) - 1
            if spaces_needed > 0:
                extra_space = (max_width - total_text_width) // spaces_needed
            else:
                extra_space = 0

            for idx, (txt, fnt) in enumerate(line):
                draw_obj.text((line_x, y), txt, font=fnt, fill=fill)
                line_x += text_width(txt, fnt)
                if idx < len(line) - 1:
                    line_x += space_width + extra_space
        y += line_height


def create_certificate(data):
    print(f"Creating certificate for: {data.get('Full Name')}")
    try:
        if not os.path.isfile(CERTIFICATE_IMAGE):
            print(f"Certificate template not found at {CERTIFICATE_IMAGE}")
            return None

        img = Image.open(CERTIFICATE_IMAGE).convert("RGB")
        draw = ImageDraw.Draw(img)

        try:
            font_bold_large = ImageFont.truetype(FONT_PATH_BOLD, FONT_SIZE_LARGE)
            font_regular = ImageFont.truetype(FONT_PATH_REGULAR, FONT_SIZE_BODY_TEXT)
            font_bold = ImageFont.truetype(FONT_PATH_BOLD, FONT_SIZE_BODY_TEXT)
        except IOError:
            print(f"Font files not found, using default font.")
            font_bold_large = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        # Draw Issue Date and ID Number in bold large font
        for field, position in FIELD_POSITIONS.items():
            text = data.get(field)
            if text:
                if field == "Issue Date":
                    text = format_date_long(text)
                draw.text(position, str(text), fill=TEXT_COLOR, font=font_bold_large)

        # Prepare body text template with placeholders
        body_text_template = (
            "This is to proudly certify {full_name} has successfully completed "
            "the professional course {course} offered by Oxdu Integrated Media School, "
            "held from {joined_date} to {end_date}. We commend their dedication and effort "
            "in acquiring advanced knowledge and practical skills in Digital Marketing, "
            "enhanced by cutting-edge artificial intelligence technologies."
        )

        # Extract values
        full_name = str(data.get("Full Name", ""))
        course = str(data.get("Course", ""))
        joined_date = format_date_dmy(data.get("Joined Date", ""))
        end_date = format_date_dmy(data.get("End Date", ""))

        # Fill template with placeholders for bold replacement
        filled_text = body_text_template.format(
            full_name=full_name,
            course=course,
            joined_date=joined_date,
            end_date=end_date
        )

        # Map placeholders to actual bold text
        bold_map = {
            full_name: full_name,
            course: course,
        }

        # Draw the paragraph with selective bold parts, letter spacing, and indent
        body_text_position = (250, 1835)
        draw_multiline_text_with_bold(
            draw_obj=draw,
            full_text=filled_text,
            bold_parts=bold_map,
            position=body_text_position,
            font_regular=font_regular,
            font_bold=font_bold,
            fill=TEXT_COLOR,
            max_width=1950,
            line_spacing=80,
            first_line_indent=0  # Optional spacing for first line
        )

        # Save certificate as PDF
        safe_name = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in full_name).replace(" ", "_")
        pdf_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}.pdf")
        print(f"Saving certificate to: {pdf_path}")
        img.save(pdf_path, "PDF", resolution=100.0)
        print("Certificate saved successfully.")
        return pdf_path

    except Exception as e:
        print(f"Error creating certificate for {data.get('Full Name')}: {e}")


def process_excel_data():
    if not os.path.isfile(EXCEL_FILE):
        print(f"Excel file not found: {EXCEL_FILE}")
        return

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active
    headers = [cell.value for cell in sheet[1]]
    print(f"Headers found in Excel: {headers}")

    for row in sheet.iter_rows(min_row=2, values_only=True):
        data = {}
        for i, header in enumerate(headers):
            if header in FIELD_POSITIONS or header in ["Full Name", "Course", "Joined Date", "End Date"]:
                data[header] = row[i]
        if data:
            create_certificate(data)


if __name__ == "__main__":
    process_excel_data()
