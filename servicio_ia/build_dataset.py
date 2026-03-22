import os
import shutil

labels_dir = "dataset/labels"
images_dir = "dataset/images"
out_dir = "keras_dataset"

os.makedirs(os.path.join(out_dir, "Rifle"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "Paraguas"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "Persona"), exist_ok=True)

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"): continue
    
    with open(os.path.join(labels_dir, label_file), 'r') as f:
        content = f.read()
        
    lines = content.strip().split('\n')
    classes = [line.split()[0] for line in lines if line.strip()]
    
    img_name = label_file.replace(".txt", ".JPG")
    if not os.path.exists(os.path.join(images_dir, img_name)):
        img_name = label_file.replace(".txt", ".jpg")
        
    src_img = os.path.join(images_dir, img_name)
    if not os.path.exists(src_img):
        print(f"No se encontró la imagen original para {label_file}")
        continue
        
    if "1" in classes: # Weapon
        dst = os.path.join(out_dir, "Rifle", img_name)
        shutil.copy2(src_img, dst)
    elif "2" in classes: # Umbrella
        dst = os.path.join(out_dir, "Paraguas", img_name)
        shutil.copy2(src_img, dst)
    elif "0" in classes: # Only Person
        dst = os.path.join(out_dir, "Persona", img_name)
        shutil.copy2(src_img, dst)
    else:
        print(f"Saltando {img_name}, no pertenece a ninguna clase.")

print("Estructuración del dataset completada exitosamente.")
