import os
import zipfile
import json
import yaml
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, session
import re
from typing import Dict, Any

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


def read_input_file(input_file) -> str:
    if input_file.filename.endswith('.zip'):
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall('temp_extracted')
            extracted_files = os.listdir('temp_extracted')
            if extracted_files:
                # Получаем все имена файлов и читаем каждый
                expressions = []
                for extracted_file in extracted_files:
                    extracted_file_path = os.path.join('temp_extracted', extracted_file)
                    with open(extracted_file_path, 'rb') as file:
                        expressions.append(read_file(file, extracted_file))  # Передаем имя файла
                return " ".join(expressions)  # Объединяем выражения из всех файлов
    else:
        return read_file(input_file, input_file.filename)  # Передаем имя файла


def read_file(file, filename: str) -> str:
    if filename.endswith('.json'):
        return json.load(file)['expression']
    elif filename.endswith('.yaml') or filename.endswith('.yml'):
        return yaml.safe_load(file)['expression']
    elif filename.endswith('.xml'):
        return read_xml(file)
    elif filename.endswith('.txt'):
        return file.read().decode('utf-8').strip()
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
        input_content = read_input_file(input_file)
        session['input_content'] = input_content
        session['input_file_extension'] = input_file.filename.split('.')[-1]  # Сохраняем расширение файла

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
    output_format = session.get('input_file_extension', 'json')  # Используем расширение файла

    print(f"Output format: {output_format}")  # Для отладки

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

        # Сохраняем результат в файл с выбранным форматом
        save_result_to_file(output_data, output_format)

        return render_template('result.html', result=result, expression=expression)
    except Exception as e:
        return render_template('result.html', result=f'Ошибка при вычислении: {str(e)}', expression=expression)


def save_result_to_file(data: Dict[str, Any], output_format: str):
    output_format = output_format.lower()  # Приводим к нижнему регистру
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
                txt_file.write(f"{key}: {value}\n")  # Сохраняем данные в формате ключ: значение
    elif output_format == 'zip':
        with zipfile.ZipFile(output_path, 'w') as zip_file:
            zip_file.writestr('result.json', json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))  # Записываем результат в zip как json
    else:
        raise ValueError("Unsupported output format")


@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html', result="Нет данных", expression="")


if __name__ == '__main__':
    app.run(debug=True)