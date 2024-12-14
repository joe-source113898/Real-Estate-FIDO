from flask import Flask, render_template
import os

app = Flask(__name__)

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for the properties page
@app.route('/properties')
def properties():
    return render_template('properties.html')

# Route for the agents page
@app.route('/agents')
def agents():
    return render_template('agents.html')

# Route for the contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    # Run the Flask server
    app.run(debug=True)
