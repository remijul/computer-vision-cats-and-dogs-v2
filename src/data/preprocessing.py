import os
from PIL import Image, ImageFile
from pathlib import Path
import shutil
import sys

# Ajouter le répertoire config au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import RAW_DATA_DIR, TEMP_DIR

ImageFile.LOAD_TRUNCATED_IMAGES = True

def clean_corrupted_images(data_path: Path) -> int:
    """Nettoyage des images corrompues"""
    num_skipped = 0
    total_files = 0
    
    for folder_name in ("Cat", "Dog"):
        folder_path = data_path / folder_name
        if not folder_path.exists():
            continue
            
        files = list(folder_path.glob("*"))
        total_files += len(files)
        
        for fpath in files:
            try:
                with Image.open(fpath) as img:
                    img.verify()
                
                if fpath.suffix.lower() in ['.jpg', '.jpeg']:
                    with open(fpath, 'rb') as f:
                        content = f.read(20)
                        if not (b"JFIF" in content or b"Exif" in content):
                            raise Exception("JPEG invalide")
                            
            except Exception:
                num_skipped += 1
                fpath.unlink()
                if num_skipped % 100 == 0:
                    print(f"Nettoyage: {num_skipped} images supprimées")
    
    print(f"Nettoyage terminé: {num_skipped}/{total_files} images supprimées")
    return num_skipped

def setup_data_directory() -> Path:
    """Configuration du répertoire de données"""
    # Créer le répertoire temporaire
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Chemin source et destination
    source_path = RAW_DATA_DIR / "PetImages"
    target_path = TEMP_DIR / "PetImages"
    
    if source_path.exists() and not target_path.exists():
        shutil.copytree(source_path, target_path)
        print(f"Données copiées vers {target_path}")
    
    return target_path if target_path.exists() else source_path