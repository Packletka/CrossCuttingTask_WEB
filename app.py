from flask import Flask, render_template, request, session
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на более безопасный ключ

def extract_operands(expression):
    # Находим все операнды и возвращаем уникальные
    return list(set(re.findall(r'\b[a-zA-Z]+\b', expression)))

def is_valid_expression(expression):
    # Простейшая проверка на валидность
    pattern = r'^[\s\w\+\-\*/\(\)]+$'
    return bool(re.match(pattern, expression))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        input_file = request.files['input_file']
        output_file = request.files['output_file']

        # Читаем содержимое входного файла
        input_content = input_file.read().decode('utf-8').strip()
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

    # Замена операндов на введенные значения
    for operand, value in values.items():
        expression = expression.replace(operand, value)

    # Вычисление результата
    try:
        result = eval(expression)

        # Сохраняем операнды и результат в out.txt
        with open("out.txt", "a") as f:  # Открываем файл в режиме добавления
            f.write(f"Операнды: {values}, Выражение: {expression}, Результат: {result}\n")

        return render_template('result.html', result=result, expression=expression)
    except Exception as e:
        return render_template('result.html', result=f'Ошибка при вычислении: {str(e)}', expression=expression)

@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html', result="Нет данных", expression="")

if __name__ == '__main__':
    app.run(debug=True)