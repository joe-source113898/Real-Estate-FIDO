import pandas as pd
import qrcode
import os

# Load the agents data
csv_file = 'agents.csv'  # Adjust this to your file's location
agents_data = pd.read_csv(csv_file)

# Ensure the 'Cellphone' column is treated as strings
agents_data['Cellphone'] = agents_data['Cellphone'].astype(str)

# Create directory for QR codes
qr_directory = 'qr_codes'
os.makedirs(qr_directory, exist_ok=True)

# Function to format cellphone numbers
def format_cellphone(cellphone):
    # Convert input to string (if not)
    cellphone = str(cellphone).strip()

    # Remove prefix '+52' if present
    if cellphone.startswith('+52'):
        cellphone = cellphone[3:]

    # Remove any non-numeric characters
    cellphone = ''.join(filter(str.isdigit, cellphone))
    
    # Check if number has exactly 12 digits after processing
    if len(cellphone) == 12:
        # Format 'XX XXXX XXXX'
        cellphone = cellphone.strip('52')
        formatted = f"{cellphone[:2]} {cellphone[2:6]} {cellphone[6:]}"
        return formatted
    else:
        # If not the expected size, return the original unformatted number
        return cellphone

# Generate HTML for the agents page with a carousel
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
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center" href="index.html">
                <img src="logo.jpg" alt="Logo" class="logo me-2">
                Fuerza Inmobiliaria de Occidente
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html#about">Sobre Nosotros</a></li>
                    <li class="nav-item"><a class="nav-link" href="agents.html">Agentes</a></li>
                    <li class="nav-item"><a class="nav-link" href="index.html#services">Servicios</a></li>
                    <li class="nav-item"><a class="nav-link" href="properties.html">Propiedades</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Contacto</a></li>
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

# Split agents into groups of 6 for the carousel
for i in range(0, len(agents_data), 6):
    group = agents_data.iloc[i:i+6]
    active_class = "active" if i == 0 else ""
    html_output += f'<div class="carousel-item {active_class}"><div class="row g-4">'

    for _, row in group.iterrows():
        name = row['Name']
        cellphone = row['Cellphone']
        first_name = name.split()[0]

        # Format the cellphone number
        formatted_cellphone = format_cellphone(cellphone)

        # Generate WhatsApp message URL
        whatsapp_url = f"https://wa.me/{cellphone}?text=Hola%20{first_name},%20te%20contacto%20desde%20la%20p%C3%A1gina%20web%20de%20FIDO%20ya%20que%20requiero%20de%20tus%20servicios."

        # Generate QR code
        qr_code_path = os.path.join(qr_directory, f"{first_name}.png")
        qr = qrcode.make(whatsapp_url)
        qr.save(qr_code_path)

        # Append agent card to HTML
        html_output += f"""
                <div class="col-md-4">
                    <div class="card agent-card shadow h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">{name}</h5>
                            <p class="card-text">Teléfono: {formatted_cellphone}</p>
                            <img src="{qr_code_path}" alt="QR WhatsApp" class="qr-code">
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

# Add navigation buttons only if there are more than 6 agents
if len(agents_data) > 6:
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

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Save the HTML file
with open("agents.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("Agents page with QR codes and carousel generated successfully.")
