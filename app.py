from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import uuid
import shutil  # Para eliminar carpetas completas

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

# Route for the agents page
@app.route('/agents')
def agents():
    return render_template('agents.html')

# Route for the contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

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
        images = property_data[-1].split(',') if property_data[-1] else []
        return render_template('property_detail.html', property=property_data, images=images)
    return "Property not found", 404

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
        
        # Save property to database first to get property ID
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO properties (name, price, operation, type, bedrooms, bathrooms, parking_spaces, area, colony, municipality, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, price, operation, property_type, bedrooms, bathrooms, parking_spaces, area, colony, municipality, ''))
        property_id = cursor.lastrowid  # Get the new property ID
        conn.commit()

        # Create folder for this property
        property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
        os.makedirs(property_folder, exist_ok=True)

        # Handle uploaded images
        images = request.files.getlist('images')
        image_filenames = []
        for image in images:
            if image and image.filename:
                ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                image.save(os.path.join(property_folder, filename))
                image_filenames.append(filename)

        # Update property with image paths
        cursor.execute('''
            UPDATE properties
            SET images = ?
            WHERE id = ?
        ''', (','.join(image_filenames), property_id))
        conn.commit()
        conn.close()

        return redirect(url_for('admin_properties'))

    return render_template('add_property.html')

# Route to edit a property
@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    property_data = get_property_by_id(property_id)
    if not property_data:
        return "Property not found", 404

    property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
    os.makedirs(property_folder, exist_ok=True)

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
        existing_images = property_data[-1].split(',') if property_data[-1] else []
        images = request.files.getlist('images')
        image_filenames = existing_images.copy()

        for image in images:
            if image and image.filename:
                ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                image.save(os.path.join(property_folder, filename))
                image_filenames.append(filename)

        # Save updated data to database
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

    return render_template('edit_property.html', property=property_data)

# Route to delete a property
@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    # Delete images folder
    property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
    if os.path.exists(property_folder):
        shutil.rmtree(property_folder)  # Delete the folder and all its contents

    # Delete property from database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_properties'))

# Route to show admin properties page
@app.route('/admin/properties')
def admin_properties():
    properties = load_properties()
    return render_template('admin_properties.html', properties=properties)

if __name__ == '__main__':
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
