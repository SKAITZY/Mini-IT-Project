from flask import Flask,redirect,url_for,render_template

# Create a FLask app instance
app = Flask(__name__)

# Definbe a route and a view function
@app.route('/')
def hello():
    return render_template('index.html')

# Run the app if this file is executed
if __name__ == '__main__':
    app.run(debug=True)
    