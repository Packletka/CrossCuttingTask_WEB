from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        input_file = request.files.get('input_file')
        output_file = request.files.get('output_file')

        if input_file and output_file:
            # Здесь вы можете обработать файлы
            return f"<h1>Файлы загружены: {input_file.filename} и {output_file.filename}</h1>"
        else:
            return "<h1>Пожалуйста, загрузите оба файла.</h1>"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

