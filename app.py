import os
import zipfile
import json
import yaml
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, session
import re
from typing import Dict, Any
from Crypto.Cipher import ARC4
import base64

app = Flask(__name__)
app.secret_key = '1S4631gyWoAyys5vVHlcjGRcRYy3O40Bzuze'


def extract_operands(expression: str) -> Dict[str, int]:
    dc: Dict[str, int] = {}
    for char in re.findall(r'\b[a-zA-Z]+\b', expression):
        dc[char] = dc.get(char, 0) + 1
    return dc.keys()


def is_valid_expression(expression: str) -> bool:
    pattern = r'^[\s\w\+\-\*/\(\)]+$'
    return bool(re.match(pattern, expression))


def decrypt_rc4(encrypted_data: bytes, key: str) -> str:
    """Decrypts a byte string using RC4."""
    cipher = ARC4.new(key.encode())
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data.decode('utf-8')  # Assuming the decrypted data is UTF-8 encoded


def read_input_file(input_file, key=None) -> str:
    if input_file.filename.endswith('.zip'):
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall('temp_extracted')
            extracted_files = os.listdir('temp_extracted')
            if extracted_files:
                expressions = []
                for extracted_file in extracted_files:
                    extracted_file_path = os.path.join('temp_extracted', extracted_file)
                    with open(extracted_file_path, 'rb') as file:
                        expressions.append(read_file(file, extracted_file, key))
                return " ".join(expressions)
    else:
        return read_file(input_file, input_file.filename, key)


def read_file(file, filename: str, key: str = None) -> str:
    if filename.endswith('.json'):
        return json.load(file)['expression']
    elif filename.endswith('.yaml') or filename.endswith('.yml'):
        return yaml.safe_load(file)['expression']
    elif filename.endswith('.xml'):
        return read_xml(file)
    elif filename.endswith('.txt'):
        return file.read().decode('utf-8').strip()
    elif filename.endswith('.enc') and key:
        encrypted_data = file.read()  # Read the file as binary
        return decrypt_rc4(encrypted_data, key)  # Decrypt without initial decoding
    else:
        raise ValueError("Unsupported file format")


def read_xml(file) -> str:
    tree = ET.parse(file)
    root = tree.getroot()
    return ' '.join([elem.text for elem in root.iter() if elem.text])


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        input_file = request.files['input_file']
        encryption_key = request.form.get('encryption_key', '').strip()

        try:
            input_content = read_input_file(input_file, encryption_key if input_file.filename.endswith('.enc') else None)
        except Exception as e:
            return f"Ошибка: {str(e)}", 400

        session['input_content'] = input_content
        session['input_file_extension'] = input_file.filename.split('.')[-1]

        if is_valid_expression(input_content):
            operands = extract_operands(input_content)
            return render_template('input_values.html', operands=operands, expression=input_content)
        else:
            return "Ошибка: некорректное выражение", 400

    return render_template('upload.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    values = request.form.to_dict()
    expression = session.get('input_content', '')
    output_format = session.get('input_file_extension', 'json')

    valid_formats = ['json', 'yaml', 'xml', 'txt', 'zip']
    if output_format not in valid_formats:
        return render_template('result.html', result='Ошибка: неподдерживаемый формат вывода', expression=expression)

    operands = extract_operands(expression)
    for operand in operands:
        if operand in values:
            expression = expression.replace(operand, values[operand])

    try:
        result = eval(expression)

        output_data = {
            "operands": values,
            "expression": expression,
            "result": result
        }

        save_result_to_file(output_data, output_format)

        return render_template('result.html', result=result, expression=expression)
    except Exception as e:
        return render_template('result.html', result=f'Ошибка при вычислении: {str(e)}', expression=expression)


def save_result_to_file(data: Dict[str, Any], output_format: str):
    output_format = output_format.lower()
    output_path = f"outputs/out.{output_format}"

    if output_format == 'json':
        with open(output_path, "w") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    elif output_format == 'yaml':
        with open(output_path, "w") as yaml_file:
            yaml.dump(data, yaml_file, allow_unicode=True)
    elif output_format == 'xml':
        with open(output_path, "w") as xml_file:
            xml_file.write('<result>\n')
            for key, value in data.items():
                xml_file.write(f'  <{key}>{value}</{key}>\n')
            xml_file.write('</result>\n')
    elif output_format == 'txt':
        with open(output_path, "w") as txt_file:
            for key, value in data.items():
                txt_file.write(f"{key}: {value}\n")
    elif output_format == 'zip':
        with zipfile.ZipFile(output_path, 'w') as zip_file:
            zip_file.writestr('result.json', json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
    else:
        raise ValueError("Unsupported output format")


@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html', result="Нет данных", expression="")


if __name__ == '__main__':
    app.run(debug=True)