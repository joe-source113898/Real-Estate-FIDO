import os
import io
import uuid
import csv
import shutil
import sqlite3
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, session, flash
from flask_mail import Mail, Message
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from email_validator import validate_email, EmailNotValidError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'images', 'properties')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', os.path.join(BASE_DIR, 'service-account-file.json'))

if not os.path.isfile(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(f"No se encontró el archivo de credenciales: {SERVICE_ACCOUNT_FILE}")

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

sheet_id = os.getenv('SPREADSHEET_ID', '1T58k_qToxNDAwKkKReLictIHztAMNxdrFeKVdSYENQc')
try:
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1
except Exception as e:
    print(f"Error al abrir la hoja de cálculo: {e}")
    worksheet = None

############################
# Initializing the DB      #
############################

DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            operation TEXT NOT NULL,
            type TEXT NOT NULL,
            bedrooms INTEGER NOT NULL,
            bathrooms REAL NOT NULL,
            parking_spaces INTEGER NOT NULL,
            area TEXT NOT NULL,
            address TEXT,
            colony TEXT NOT NULL,
            municipality TEXT NOT NULL,
            map_location TEXT,
            status TEXT NOT NULL DEFAULT 'Normal',
            images TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_properties():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties")
    properties = cursor.fetchall()
    conn.close()
    return properties

def get_property_by_id(property_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    property_data = cursor.fetchone()
    conn.close()
    return property_data

def load_filtered_properties(operation=None, property_type=None, min_price=None, max_price=None,
                             bedrooms=None, bathrooms=None, parking=None, colony=None,
                             municipality=None, limit=None, offset=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM properties WHERE status = 'Normal'"
    params = []

    if operation and operation.strip():
        query += " AND operation = ?"
        params.append(operation)
    if property_type and property_type.strip():
        query += " AND type = ?"
        params.append(property_type)
    if min_price and min_price.strip().replace('.', '', 1).isdigit():
        query += " AND price >= ?"
        params.append(float(min_price))
    if max_price and max_price.strip().replace('.', '', 1).isdigit():
        query += " AND price <= ?"
        params.append(float(max_price))
    if bedrooms and bedrooms.strip().isdigit():
        query += " AND bedrooms = ?"
        params.append(int(bedrooms))
    if bathrooms and bathrooms.strip().replace('.', '', 1).isdigit():
        query += " AND bathrooms = ?"
        params.append(float(bathrooms))
    if parking and parking.strip().isdigit():
        query += " AND parking_spaces = ?"
        params.append(int(parking))
    if colony and colony.strip():
        query += " AND colony LIKE ?"
        params.append(f"%{colony}%")
    if municipality and municipality.strip():
        query += " AND municipality LIKE ?"
        params.append(f"%{municipality}%")

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)

    cursor.execute(query, params)
    filtered_properties = cursor.fetchall()
    conn.close()

    return filtered_properties

def count_filtered_properties(operation=None, property_type=None, min_price=None, max_price=None,
                              bedrooms=None, bathrooms=None, parking=None, colony=None,
                              municipality=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM properties WHERE status = 'Normal'"
    params = []

    if operation and operation.strip():
        query += " AND operation = ?"
        params.append(operation)
    if property_type and property_type.strip():
        query += " AND type = ?"
        params.append(property_type)
    if min_price and min_price.strip().replace('.', '', 1).isdigit():
        query += " AND price >= ?"
        params.append(float(min_price))
    if max_price and max_price.strip().replace('.', '', 1).isdigit():
        query += " AND price <= ?"
        params.append(float(max_price))
    if bedrooms and bedrooms.strip().isdigit():
        query += " AND bedrooms = ?"
        params.append(int(bedrooms))
    if bathrooms and bathrooms.strip().replace('.', '', 1).isdigit():
        query += " AND bathrooms = ?"
        params.append(float(bathrooms))
    if parking and parking.strip().isdigit():
        query += " AND parking_spaces = ?"
        params.append(int(parking))
    if colony and colony.strip():
        query += " AND colony LIKE ?"
        params.append(f"%{colony}%")
    if municipality and municipality.strip():
        query += " AND municipality LIKE ?"
        params.append(f"%{municipality}%")

    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()

    return count

AGENTS_CSV_PATH = os.path.join(BASE_DIR, 'agents.csv')

def load_agents():
    agents = []
    try:
        with open(AGENTS_CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                agents.append({'Name': row['Name'], 'Cellphone': row['Cellphone']})
    except FileNotFoundError:
        print(f"El archivo {AGENTS_CSV_PATH} no se encontró.")
    return agents

############################
#   PUBLIC ROUTES          #
############################

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agents', endpoint='agents')
def agents_page():
    return render_template('agents.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/properties', methods=['GET'])
def properties():
    operation = request.args.get('operation')
    property_type = request.args.get('type')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    bedrooms = request.args.get('bedrooms')
    bathrooms = request.args.get('bathrooms')
    parking = request.args.get('parking')
    colony = request.args.get('colony')
    municipality = request.args.get('municipality')

    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    per_page = 15
    offset = (page - 1) * per_page

    filtered_props = load_filtered_properties(
        operation=operation,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
        colony=colony,
        municipality=municipality,
        limit=per_page,
        offset=offset
    )

    total_properties = count_filtered_properties(
        operation=operation,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
        colony=colony,
        municipality=municipality
    )
    total_pages = (total_properties + per_page - 1) // per_page

    return render_template(
        'properties.html',
        properties=filtered_props,
        page=page,
        total_pages=total_pages,
        filters={
            'operation': operation,
            'type': property_type,
            'min_price': min_price,
            'max_price': max_price,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'parking': parking,
            'colony': colony,
            'municipality': municipality
        }
    )

############################
#     SLUGIFY UTIL         #
############################

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text

@app.template_filter('slugify')
def slugify_filter(s):
    return slugify(s)

############################
#   PROPERTY DETAIL (Slug) #
############################

@app.route('/property/<int:property_id>/<slug>')
def property_detail(property_id, slug):
    property_data = get_property_by_id(property_id)
    if not property_data:
        flash('Propiedad no encontrada.', 'danger')
        return redirect(url_for('index')), 404

    # Generar slug real a partir del nombre de la propiedad
    generated_slug = slugify(property_data[1])
    if slug != generated_slug:
        # Redirigir con el slug correcto si difiere
        return redirect(url_for('property_detail', property_id=property_id, slug=generated_slug), code=301)

    images = property_data[14].split(',') if property_data[14] else []
    agents = load_agents()
    return render_template('property_detail.html', property=property_data, images=images, agents=agents)

############################
#   PROPERTY PDF           #
############################

@app.route('/property/<int:property_id>/pdf', methods=['GET'])
def property_pdf(property_id):
    property_data = get_property_by_id(property_id)
    if not property_data:
        flash('Propiedad no encontrada.', 'danger')
        abort(404, description="Propiedad no encontrada")

    images = property_data[14].split(',') if property_data[14] else []

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, property_data[1], ln=True, align='C')
    pdf.ln(10)

    for image in images:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id), image)
        if os.path.exists(image_path):
            try:
                pdf.image(image_path, x=(pdf.w - 100) / 2, w=100)
                pdf.ln(10)
            except RuntimeError as e:
                print(f"Error al cargar la imagen {image_path}: {e}")

    pdf.set_font("Arial", size=12)

    banos = float(property_data[6])
    banos_str = str(int(banos)) if banos.is_integer() else str(banos)

    details = [
        f"Precio: ${property_data[2]:,.0f} MXN",
        f"Tipo de Operación: {property_data[3].capitalize()}",
        f"Tipo de Propiedad: {property_data[4].capitalize()}",
        f"Recámara(s): {property_data[5]}",
        f"Baño(s): {banos_str}",
        f"Espacio para auto(s): {property_data[7]}",
        f"Área: {property_data[8]} m²",
        f"Dirección: {property_data[9]}, {property_data[10]}, {property_data[11]}"
    ]

    for detail in details:
        pdf.cell(0, 10, detail, ln=True, align='C')

    pdf_content = pdf.output(dest='S').encode('latin1')
    pdf_buffer = io.BytesIO(pdf_content)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Propiedad_{property_id}.pdf",
        mimetype='application/pdf'
    )

############################
#        LOGIN/LOGOUT      #
############################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_user = os.getenv('ADMIN_USER')
        admin_pass = os.getenv('ADMIN_PASSWORD')

        if username == admin_user and password == admin_pass:
            session['logged_in'] = True
            session['welcome_message'] = True
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('admin_properties'))
        else:
            flash("Credenciales inválidas.", 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

############################
#     ADMIN ROUTES         #
############################

@app.route('/admin/properties')
@admin_required
def admin_properties():
    properties = load_properties()
    if session.get('welcome_message'):
        flash('Bienvenido al panel de administración.', 'info')
        session.pop('welcome_message')
    return render_template('admin_properties.html', properties=properties)

@app.route('/admin/properties/add', methods=['GET', 'POST'])
@admin_required
def add_property():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        operation = request.form['operation']
        property_type = request.form['type']
        bedrooms = request.form['bedrooms']
        bathrooms = request.form['bathrooms']
        parking_spaces = request.form['parking_spaces']
        area = request.form['area']
        address = request.form.get('address', '')
        colony = request.form['colony']
        municipality = request.form['municipality']
        map_location = request.form.get('map_location', '')

        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO properties (name, price, operation, type, bedrooms, bathrooms, parking_spaces, area, address, colony, municipality, map_location, status, images)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Normal', ?)
            ''', (name, price, operation, property_type, bedrooms, bathrooms, parking_spaces,
                  area, address, colony, municipality, map_location, ''))
            property_id = cursor.lastrowid
            conn.commit()

            property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
            os.makedirs(property_folder, exist_ok=True)

            images = request.files.getlist('images')
            image_filenames = []
            for image in images:
                if image and image.filename:
                    ext = os.path.splitext(image.filename)[1]
                    filename = f"{uuid.uuid4()}{ext}"
                    image.save(os.path.join(property_folder, filename))
                    image_filenames.append(filename)

            cursor.execute('''
                UPDATE properties
                SET images = ?
                WHERE id = ?
            ''', (','.join(image_filenames), property_id))
            conn.commit()
            conn.close()

            flash('Propiedad agregada exitosamente.', 'success')
            return redirect(url_for('admin_properties'))
        except Exception as e:
            flash(f'Error al agregar la propiedad: {e}', 'danger')
            return redirect(request.url)

    return render_template('add_property.html')

@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
@admin_required
def edit_property(property_id):
    property_data = get_property_by_id(property_id)
    if not property_data:
        flash('Propiedad no encontrada.', 'danger')
        return redirect(url_for('admin_properties'))

    property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
    os.makedirs(property_folder, exist_ok=True)

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        operation = request.form['operation']
        property_type = request.form['type']
        bedrooms = request.form['bedrooms']
        bathrooms = request.form['bathrooms']
        parking_spaces = request.form['parking_spaces']
        area = request.form['area']
        address = request.form.get('address', '')
        colony = request.form['colony']
        municipality = request.form['municipality']
        map_location = request.form.get('map_location', '')

        existing_images = property_data[14].split(',') if property_data[14] else []
        images = request.files.getlist('images')
        image_filenames = existing_images.copy()

        for image in images:
            if image and image.filename:
                ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                image.save(os.path.join(property_folder, filename))
                image_filenames.append(filename)

        status = request.form.get('status', property_data[13])

        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE properties
                SET name = ?, price = ?, operation = ?, type = ?, bedrooms = ?, bathrooms = ?,
                    parking_spaces = ?, area = ?, address = ?, colony = ?, municipality = ?,
                    map_location = ?, status = ?, images = ?
                WHERE id = ?
            ''', (name, price, operation, property_type, bedrooms, bathrooms, parking_spaces,
                  area, address, colony, municipality, map_location, status,
                  ','.join(image_filenames), property_id))
            conn.commit()
            conn.close()

            flash('Propiedad actualizada exitosamente.', 'success')
            return redirect(url_for('admin_properties'))
        except Exception as e:
            flash(f'Error al actualizar la propiedad: {e}', 'danger')
            return redirect(request.url)

    return render_template('edit_property.html', property=property_data)

@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
@admin_required
def delete_property(property_id):
    try:
        property_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id))
        if os.path.exists(property_folder):
            shutil.rmtree(property_folder)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        conn.commit()
        conn.close()

        flash('Propiedad eliminada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar la propiedad: {e}', 'danger')

    return redirect(url_for('admin_properties'))

@app.route('/admin/properties/delete_image/<int:property_id>', methods=['POST'])
@admin_required
def delete_image(property_id):
    filename = request.form.get('filename')
    if not filename:
        flash('Nombre de archivo no proporcionado.', 'danger')
        return redirect(request.url), 400

    property_data = get_property_by_id(property_id)
    if not property_data:
        flash('Propiedad no encontrada.', 'danger')
        return redirect(url_for('admin_properties')), 404

    existing_images = property_data[14].split(',') if property_data[14] else []
    if filename not in existing_images:
        flash('Imagen no encontrada.', 'danger')
        return redirect(url_for('edit_property', property_id=property_id)), 404

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(property_id), filename)
    if os.path.exists(image_path):
        os.remove(image_path)

    updated_images = [img for img in existing_images if img != filename]
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE properties
            SET images = ?
            WHERE id = ?
        ''', (','.join(updated_images), property_id))
        conn.commit()
        conn.close()
        flash('Imagen eliminada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar la imagen: {e}', 'danger')

    return redirect(url_for('edit_property', property_id=property_id))

@app.route('/admin/properties/delete_all', methods=['POST'])
@admin_required
def delete_all_properties():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM properties")
        conn.commit()
        conn.close()

        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        flash('Todas las propiedades han sido eliminadas.', 'success')
    except Exception as e:
        flash(f'Error al eliminar todas las propiedades: {e}', 'danger')

    return redirect(url_for('admin_properties'))

@app.route('/admin/properties/toggle_status/<int:property_id>', methods=['POST'])
@admin_required
def toggle_status(property_id):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM properties WHERE id = ?", (property_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            flash('Propiedad no encontrada.', 'danger')
            return redirect(url_for('admin_properties')), 404

        current_status = result[0]
        new_status = "En pausa" if current_status == "Normal" else "Normal"
        cursor.execute("UPDATE properties SET status = ? WHERE id = ?", (new_status, property_id))
        conn.commit()
        conn.close()
        flash(f"Estado de la propiedad cambiado a '{new_status}'.", 'success')
    except Exception as e:
        flash(f'Error al cambiar el estado de la propiedad: {e}', 'danger')

    return redirect(url_for('admin_properties'))

############################
#  GENERAL PDF (All Props) #
############################

@app.route('/properties/pdf', methods=['GET'])
def properties_pdf():
    operation = request.args.get('operation')
    property_type = request.args.get('type')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    bedrooms = request.args.get('bedrooms')
    bathrooms = request.args.get('bathrooms')
    parking = request.args.get('parking')
    colony = request.args.get('colony')
    municipality = request.args.get('municipality')

    filtered_props = load_filtered_properties(
        operation=operation,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking=parking,
        colony=colony,
        municipality=municipality
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for prop in filtered_props:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, prop[1], ln=True, align='C')

        pdf.set_font("Arial", size=12)
        images = prop[14].split(',') if prop[14] else []
        if images and images[0]:
            property_image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(prop[0]), images[0])
            if os.path.exists(property_image_path):
                image_width = 100
                x_position = (pdf.w - image_width) / 2
                try:
                    pdf.image(property_image_path, x=x_position, y=30, w=image_width)
                except RuntimeError as e:
                    print(f"Error al cargar la imagen: {e}")
                pdf.ln(75)
            else:
                pdf.ln(10)
        else:
            pdf.ln(10)

        pdf.cell(0, 10, f"Precio: ${int(prop[2]):,} MXN", ln=True, align='C')
        pdf.cell(0, 10, f"Tipo de Operación: {prop[3].capitalize()}", ln=True, align='C')
        pdf.cell(0, 10, f"Tipo de Propiedad: {prop[4].capitalize()}", ln=True, align='C')
        pdf.cell(0, 10, f"Recámara(s): {prop[5]}", ln=True, align='C')

        valor = float(prop[6])
        valor_str = str(int(valor)) if valor.is_integer() else str(valor)
        pdf.cell(0, 10, f"Baño(s): {valor_str}", ln=True, align='C')

        pdf.cell(0, 10, f"Espacio para auto(s): {prop[7]}", ln=True, align='C')
        pdf.cell(0, 10, f"Área: {prop[8]} m²", ln=True, align='C')
        pdf.cell(0, 10, f"Dirección: {prop[9]}", ln=True, align='C')
        pdf.cell(0, 10, f"Colonia: {prop[10]}", ln=True, align='C')
        pdf.cell(0, 10, f"Municipio: {prop[11]}", ln=True, align='C')
        pdf.ln(10)

    pdf_content = pdf.output(dest='S').encode('latin1')
    pdf_buffer = io.BytesIO(pdf_content)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="Propiedades_disponibles.pdf",
        mimetype='application/pdf'
    )

############################
#  CONTACT ROUTE (FORM)    #
############################

@app.route('/send_contact', methods=['POST'])
def send_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    phonenumber = request.form.get('phonenumber')
    message = request.form.get('message')
    property_url = request.form.get('property_url', '')

    if not name or not email or not phonenumber or not message:
        flash('Por favor, completa todos los campos del formulario.', 'danger')
        return redirect(request.referrer or url_for('index'))

    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        flash(str(e), 'danger')
        return redirect(request.referrer or url_for('index'))

    if not phonenumber.isdigit() or len(phonenumber) < 10:
        flash('Por favor, ingresa un número de teléfono con al menos 10 dígitos.', 'danger')
        return redirect(request.referrer or url_for('index'))

    subject = f"Nuevo mensaje de {name} desde Fuerza Inmobiliaria de Occidente"
    body = f"""
    Has recibido un nuevo mensaje desde el sitio web.

    Detalles del remitente:
    Nombre: {name}
    Correo electrónico: {email}
    Teléfono: {phonenumber}

    Mensaje:
    {message}
    """
    if property_url:
        body += f"\nEnlace de la propiedad:\n{property_url}"

    try:
        msg = Message(subject=subject, recipients=['servicios.inmobiliarios.zmg1138@gmail.com'], body=body)
        mail.send(msg)

        if worksheet:
            timezone_guadalajara = ZoneInfo("America/Mexico_City")
            row = [
                name,
                email,
                phonenumber,
                message,
                property_url,
                datetime.now(timezone_guadalajara).strftime('%Y-%m-%d %H:%M:%S')
            ]
            worksheet.append_row(row)
        else:
            print("La hoja de cálculo no está configurada correctamente.")

        flash('Tu mensaje ha sido enviado exitosamente.', 'success')
    except Exception as e:
        print(f"Error al enviar el correo o registrar en Sheets: {e}")
        flash('Ocurrió un error al enviar tu mensaje. Por favor, inténtalo de nuevo más tarde.', 'danger')

    return redirect(request.referrer or url_for('index'))

############################
#     DEBUG SHEETS         #
############################

@app.route('/debug_sheets')
def debug_sheets():
    if not worksheet:
        flash("No se pudo autenticar con Google Sheets.", 'danger')
        return redirect(url_for('index'))
    try:
        spreadsheets = gc.openall()
        sheet_names = [sheet.title for sheet in spreadsheets]
        flash(f"Hojas de cálculo accesibles: {', '.join(sheet_names)}", 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error al listar hojas de cálculo: {e}", 'danger')
        return redirect(url_for('index'))

############################
#       MAIN APP           #
############################

if __name__ == '__main__':
    app.run(debug=True)

application = app
