import pandas as pd
import qrcode
import os


csv_file = 'agents.csv'
agents_data = pd.read_csv(csv_file)

agents_data['Cellphone'] = agents_data['Cellphone'].astype(str)

qr_directory = 'static/qr_codes'
os.makedirs(qr_directory, exist_ok=True)

def format_cellphone(cellphone):
    cellphone = str(cellphone).strip()

    if cellphone.startswith('+52'):
        cellphone = cellphone[3:]

    cellphone = ''.join(filter(str.isdigit, cellphone))
    
    if len(cellphone) == 12:
        cellphone = cellphone.strip('52')

        formatted = f"{cellphone[:2]} {cellphone[2:6]} {cellphone[6:]}"
        return formatted
    else:
        return cellphone

total_agents = len(agents_data)

html_output = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentes - Fuerza Inmobiliaria de Occidente</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center" href="{{ url_for('index') }}">
                <img src="{{ url_for('static', filename='images/logo_dark_background.png') }}" alt="Logo" class="logo me-2">
                Fuerza Inmobiliaria de Occidente
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}#about">Sobre Nosotros</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('agents') }}">Agentes</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}#services">Servicios</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('properties') }}">Propiedades</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('contact') }}">Contacto</a></li>
                </ul>
                <!-- Social Media Icons in Navbar -->
                <div class="d-flex ms-lg-3">
                    <a href="https://facebook.com" target="_blank" class="text-white me-3"><i class="bi bi-facebook"></i></a>
                    <a href="https://twitter.com" target="_blank" class="text-white me-3"><i class="bi bi-twitter"></i></a>
                    <a href="https://instagram.com" target="_blank" class="text-white"><i class="bi bi-instagram"></i></a>
                </div>
            </div>
        </div>
    </nav>

    <header class="hero-section text-white text-center py-5">
        <div class="container">
            <h1 class="display-4 fw-bold">Nuestros Agentes</h1>
            <p class="lead mt-3">Conoce a nuestro equipo de expertos listos para ayudarte.</p>
        </div>
    </header>

    <main class="py-5">
        <div class="container">
            <div id="agentsCarousel" class="carousel slide" data-bs-ride="carousel">
                <div class="carousel-inner">
"""

for i in range(0, total_agents, 6):
    group = agents_data.iloc[i:i+6]
    active_class = "active" if i == 0 else ""
    html_output += f'<div class="carousel-item {active_class}"><div class="row g-4">'

    for _, row in group.iterrows():
        name = row['Name']
        cellphone = row['Cellphone']
        first_name = name.split()[0]

        formatted_cellphone = format_cellphone(cellphone)

        whatsapp_url = f"https://wa.me/{cellphone}?text=Hola%20{first_name},%20te%20contacto%20desde%20la%20p%C3%A1gina%20web%20de%20FIDO%20ya%20que%20requiero%20de%20tus%20servicios."

        qr_code_path = os.path.join(qr_directory, f"{first_name}.png")
        qr = qrcode.make(whatsapp_url)
        qr.save(qr_code_path)

        html_output += f"""
                <div class="col-md-4">
                    <div class="card agent-card shadow h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">{name}</h5>
                            <p class="card-text">Teléfono: {formatted_cellphone}</p>
                            <img src="static/qr_codes/{first_name}.png" alt="QR WhatsApp" class="qr-code">
                            <p class="mt-2">Escanea este QR para mandar mensaje directo al agente en WhatsApp</p>
                            <a href="tel:+{cellphone}" class="btn btn-primary mt-3">Llamar</a>
                        </div>
                    </div>
                </div>
        """

    html_output += "</div></div>"

html_output += """
                </div>
"""

if total_agents > 6:
    html_output += """
                <button class="carousel-control-prev" type="button" data-bs-target="#agentsCarousel" data-bs-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Anterior</span>
                </button>
                <button class="carousel-control-next" type="button" data-bs-target="#agentsCarousel" data-bs-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Siguiente</span>
                </button>
    """

html_output += """
            </div>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2024 Fuerza Inmobiliaria de Occidente. Todos los derechos reservados.</p>
            <div class="social-icons">
                <a href="https://facebook.com" target="_blank"><i class="bi bi-facebook"></i></a>
                <a href="https://twitter.com" target="_blank"><i class="bi bi-twitter"></i></a>
                <a href="https://instagram.com" target="_blank"><i class="bi bi-instagram"></i></a>
            </div>
        </div>
    </footer> 

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

with open("templates/agents.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("Agents page with QR codes and carousel generated successfully.")
