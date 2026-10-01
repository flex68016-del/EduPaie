"""
Script pour convertir l'icône SVG en ICO pour PyInstaller
PyInstaller ne peut pas convertir directement SVG en ICO, donc nous devons
créer un fichier .ico manuellement.
Utilise cairosvg et PIL (Pillow) qui sont déjà installés.
"""

from pathlib import Path
from PIL import Image
import cairosvg
import io

# Chemins
script_dir = Path(__file__).parent.parent
svg_path = script_dir / "edupaie" / "assets" / "edupaie-icon.svg"
ico_path = script_dir / "edupaie" / "assets" / "edupaie-icon.ico"

# Tailles pour l'icône Windows
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
icon_images = []

print(f"[INFO] Conversion de {svg_path} vers ICO...")

for size in icon_sizes:
    # Convertir SVG → PNG avec la taille souhaitée
    png_data = cairosvg.svg2png(url=str(svg_path), output_width=size[0], output_height=size[1])
    
    # Ouvrir l'image PIL depuis les bytes
    img = Image.open(io.BytesIO(png_data))
    icon_images.append(img)

# Sauvegarder en .ico
icon_images[0].save(
    str(ico_path),
    format='ICO',
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
)

print(f"[INFO] Icône créée : {ico_path}")
