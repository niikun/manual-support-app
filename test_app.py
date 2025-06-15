import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return f'''
    <h1>Railway Test App</h1>
    <p>Port: {os.environ.get('PORT', 'Not set')}</p>
    <p>OpenAI Key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not set'}</p>
    <p>Secret Key: {'Set' if os.environ.get('SECRET_KEY') else 'Not set'}</p>
    <p>Python Version: {os.sys.version}</p>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'port': os.environ.get('PORT')}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)