import os

import PyPDF2


def extract_text_from_pdf(file_path):
    pdf_reader = PyPDF2.PdfReader(file_path)
    text_data = ""
    for page in pdf_reader.pages:
        text_data += page.extract_text()
    return text_data


def save_file(file, file_path):
    # 파일 저장 폴더 생성
    save_folder = os.path.dirname(file_path)
    os.makedirs(save_folder, exist_ok=True)

    # 파일 저장
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
