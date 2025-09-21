# app.py
from flask import Flask, request, jsonify, render_template
from terminal import PythonTerminal  # import your class from terminal.py

app = Flask(__name__)
terminal = PythonTerminal()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    command = data.get('command', '') if data else ''
    result = terminal.execute_command(command)
    return jsonify(result)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
