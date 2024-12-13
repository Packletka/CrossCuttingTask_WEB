import os
from flask import Flask, render_template, request, session
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def extract_operands(expression):
    return list(set(re.findall(r'\b[a-zA-Z]+\b', expression)))

def is_valid_expression(expression):
    pattern = r'^[\s\w\+\-\*/\(\)]+$'
    return bool(re.match(pattern, expression))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        input_file = request.files['input_file']
        input_content = input_file.read().decode('utf-8').strip()
        session['input_content'] = input_content

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

    for operand, value in values.items():
        expression = expression.replace(operand, value)

    try:
        result = eval(expression)

        # Убедимся, что папка для выходного файла существует
        output_dir = 'outputs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Записываем результат в out.txt
        with open(os.path.join(output_dir, "out.txt"), "a") as f:
            f.write(f"Операнды: {values}, Выражение: {expression}, Результат: {result}\n")

        # Сохраняем результат в выходной файл
        if 'output_file' in request.files:
            output_file = request.files['output_file']
            output_file_path = os.path.join(output_dir, output_file.filename)
            with open(output_file_path, "w") as f:
                f.write(f"Выражение: {expression}\nРезультат: {result}\n")

        return render_template('result.html', result=result, expression=expression)
    except Exception as e:
        return render_template('result.html', result=f'Ошибка при вычислении: {str(e)}', expression=expression)

@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html', result="Нет данных", expression="")

if __name__ == '__main__':
    app.run(debug=True)