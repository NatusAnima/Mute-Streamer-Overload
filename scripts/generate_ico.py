import os
from pathlib import Path
from cairosvg import svg2png
from PIL import Image
import io

def generate_ico():
    # Get the assets directory
    assets_dir = Path(__file__).parent.parent / 'assets'
    svg_path = assets_dir / 'icon.svg'
    
    if not svg_path.exists():
        print(f"SVG file not found: {svg_path}")
        return
    
    # Generate PNGs at different sizes
    sizes = [16, 32, 48, 64, 128, 256]
    
    print("Generating icon sizes:", sizes)
    
    # First, generate the largest size for best quality
    print("Generating base image at 256x256...")
    png_data = svg2png(
        url=str(svg_path),
        output_width=256,
        output_height=256,
        dpi=96
    )
    base_image = Image.open(io.BytesIO(png_data))
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')
    
    # Generate and save each size separately
    for size in sizes:
        print(f"\nProcessing {size}x{size} icon...")
        # Resize the base image
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save as ICO with size in filename
        ico_path = assets_dir / f'icon_{size}x{size}.ico'
        print(f"Saving to {ico_path}")
        resized.save(ico_path, format='ICO')
        
        # Verify the saved ICO
        with Image.open(ico_path) as ico:
            sizes_set = ico.ico.sizes()
            print(f"Verified {ico_path} contains sizes: {sizes_set}")
    
    print("\nAll icon sizes have been generated separately.")
    print("You can find them in the assets directory with names like:")
    for size in sizes:
        print(f"  - icon_{size}x{size}.ico")

if __name__ == "__main__":
    generate_ico() 