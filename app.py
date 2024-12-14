import os
import zipfile
from flask import Flask, render_template, request, session
import re
from typing import Dict

app = Flask(__name__)
app.secret_key = '1S4631gyWoAyys5vVHlcjGRcRYy3O40Bzuze'


def extract_operands(expression):
    dc: Dict[str, int] = {}
    # Формальный счетчик
    for char in re.findall(r'\b[a-zA-Z]+\b', expression):
        dc[char] = dc.get(char, 0) + 1
    return dc.keys()


def is_valid_expression(expression):
    pattern = r'^[\s\w\+\-\*/\(\)]+$'
    return bool(re.match(pattern, expression))


def read_input_file(input_file):
    if input_file.filename.endswith('.zip'):
        # Если файл — архив, разархивируем его
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall('temp_extracted')
            # Предполагаем, что внутри архива только один файл
            extracted_files = os.listdir('temp_extracted')
            if extracted_files:
                with open(os.path.join('temp_extracted', extracted_files[0]), 'r') as f:
                    return f.read().strip()
    else:
        # Если это обычный файл, просто читаем его содержимое
        return input_file.read().decode('utf-8').strip()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        input_file = request.files['input_file']

        # Читаем содержимое входного файла
        input_content = read_input_file(input_file)
        session['input_content'] = input_content  # Сохраняем содержимое в сессии

        # Проверяем валидность выражения
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

    # Порядок назначения значений операндам
    operands = extract_operands(expression)
    for operand in operands:
        if operand in values:
            expression = expression.replace(operand, values[operand])

    # Вычисление результата
    try:
        result = eval(expression)

        # Записываем результат в out.txt
        with open("outputs/out.txt", "a") as f:
            f.write(f"Операнды: {values}, Выражение: {expression}, Результат: {result}\n")

        return render_template('result.html', result=result, expression=expression)
    except Exception as e:
        return render_template('result.html', result=f'Ошибка при вычислении: {str(e)}', expression=expression)


@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html', result="Нет данных", expression="")


if __name__ == '__main__':
    app.run(debug=True)
