from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/properties'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to load all properties
def load_properties():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties")
    properties = cursor.fetchall()
    conn.close()
    return properties

# Function to get a property by ID
def get_property_by_id(property_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    property_data = cursor.fetchone()
    conn.close()
    return property_data

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for the properties page
@app.route('/properties')
def properties():
    properties = load_properties()
    return render_template('properties.html', properties=properties)

# Route for the property detail page
@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property_data = get_property_by_id(property_id)
    if property_data:
        images = property_data[-1].split(',')  # Extract images from the images column
        return render_template('property_detail.html', property=property_data, images=images)
    return "Property not found", 404

# Route for the agents page
@app.route('/agents')
def agents():
    return render_template('agents.html')

# Route for the contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route for the admin properties page
@app.route('/admin/properties')
def admin_properties():
    properties = load_properties()
    return render_template('admin_properties.html', properties=properties)

# Route to add a new property
@app.route('/admin/properties/add', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        price = request.form['price']
        operation = request.form['operation']
        property_type = request.form['type']
        bedrooms = request.form['bedrooms']
        bathrooms = request.form['bathrooms']
        parking_spaces = request.form['parking_spaces']
        area = request.form['area']
        colony = request.form['colony']
        municipality = request.form['municipality']

        # Handle uploaded images
        images = request.files.getlist('images')
        image_filenames = []
        for image in images:
            filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filenames.append(filename)

        # Save property to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO properties (name, price, operation, type, bedrooms, bathrooms, parking_spaces, area, colony, municipality, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, price, operation, property_type, bedrooms, bathrooms, parking_spaces, area, colony, municipality, ','.join(image_filenames)))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_properties'))

    return render_template('add_property.html')

# Route to edit a property
@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    if request.method == 'POST':
        # Update property data
        name = request.form['name']
        price = request.form['price']
        operation = request.form['operation']
        property_type = request.form['type']
        bedrooms = request.form['bedrooms']
        bathrooms = request.form['bathrooms']
        parking_spaces = request.form['parking_spaces']
        area = request.form['area']
        colony = request.form['colony']
        municipality = request.form['municipality']

        # Handle uploaded images
        images = request.files.getlist('images')
        image_filenames = []
        for image in images:
            filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filenames.append(filename)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE properties
            SET name = ?, price = ?, operation = ?, type = ?, bedrooms = ?, bathrooms = ?, parking_spaces = ?, area = ?, colony = ?, municipality = ?, images = ?
            WHERE id = ?
        ''', (name, price, operation, property_type, bedrooms, bathrooms, parking_spaces, area, colony, municipality, ','.join(image_filenames), property_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_properties'))

    property_data = get_property_by_id(property_id)
    return render_template('edit_property.html', property=property_data)

# Route to delete a property
@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch images associated with the property
    cursor.execute("SELECT images FROM properties WHERE id = ?", (property_id,))
    images = cursor.fetchone()[0].split(',')

    # Delete images from the file system
    for image in images:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete property from the database
    cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_properties'))

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    def init_db():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                operation TEXT NOT NULL,
                type TEXT NOT NULL,
                bedrooms INTEGER NOT NULL,
                bathrooms INTEGER NOT NULL,
                parking_spaces INTEGER NOT NULL,
                area INTEGER NOT NULL,
                colony TEXT NOT NULL,
                municipality TEXT NOT NULL,
                images TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    init_db()
    app.run(debug=True)
