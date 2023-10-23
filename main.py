import os
from PIL import Image
Image.LOAD_TRUNCATED_IMAGES = True

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

VTFCMD_PATH = f"{CURRENT_PATH}\\vtfcmd"
INPUT_FOLDER = f"{CURRENT_PATH}\\input"

NORMAL_ALIASES = ["_n", "_nm", "bump", "-n", "_b", "_nrm", "normal"]
GLOW_ALIASES = ["_gl", "glow"]
SPECULAR_ALIASES = ["_spec", "_sp", "-spec", "specular"]

def convert_vtf_to_png(vtf_path, output_folder):
    os.system(f'vtfcmd.exe -file "{vtf_path}" -output "{output_folder}" -exportformat "png" -silent')

def convert_png_to_vtf(png_path, output_folder, use_alpha, resize_width = 0, resize_height = 0):
    prompt = f'vtfcmd.exe -file "{png_path}" -output "{output_folder}" -format "dxt5" -silent'

    if resize_width != 0 and resize_height != 0:
        prompt += f' -resize -rmethod "nearest" -rfilter "cubic" -rwidth "{resize_width}" -rheight "{resize_height}"'

    if use_alpha:
        prompt += ' -format "dxt5" -alphaformat "dxt5"'
    else:
        prompt += ' -format "dxt1" -alphaformat "dxt1"'

    os.system(prompt)

def check_alpha(png_path):
    img = Image.open(png_path)

    if img.mode != "RGBA":
        return False
                                           
    alpha = img.getchannel('A')

    if alpha.getextrema() == (255, 255):
        return False
    
    return True

def get_image_size(png_path):
    img = Image.open(png_path)

    return img.size

def optimize_in_place(vtf_path, max_width = 0, max_height = 0):
    vtf_folder = os.path.dirname(vtf_path)
    file_name = os.path.basename(vtf_path)
    file_no_ext = os.path.splitext(file_name)[0]

    print(f" - Optimizing {file_name}")

    convert_vtf_to_png(vtf_path, vtf_folder)

    use_alpha = check_alpha(f"{vtf_folder}\\{file_no_ext}.png")
    #print(f"   - Using alpha: {use_alpha}")

    if max_width != 0 and max_height != 0:
        image_size = get_image_size(f"{vtf_folder}\\{file_no_ext}.png")

        if image_size[0] > max_width or image_size[1] > max_height:
            aspect_ratio = image_size[0] / image_size[1]

            if aspect_ratio > 1:
                max_height = int(max_width / aspect_ratio)
            else:
                max_width = int(max_height * aspect_ratio)

            print(f"   - Resizing image to {max_width}x{max_height}")

        max_width = min(image_size[0], max_width)
        max_height = min(image_size[1], max_height)

    convert_png_to_vtf(f"{vtf_folder}\\{file_no_ext}.png", vtf_folder, use_alpha, max_width, max_height)

    os.remove(f"{vtf_folder}\\{file_no_ext}.png")  

def optimize_folder(input_folder, max_resolutions = {"diffuse": (4096, 4096), "normal": (4096, 4096), "glow": (4096, 4096), "specular": (4096, 4096)}):
    print(f"\nOptimizing folder {input_folder}")

    for file in os.listdir(input_folder):
        if os.path.splitext(file)[1] != ".vtf":
            continue

        max_width = 0
        max_height = 0

        for alias in NORMAL_ALIASES:
            if alias in file:
                max_width = max_resolutions["normal"][0]
                max_height = max_resolutions["normal"][1]
                break

        for alias in GLOW_ALIASES:
            if alias in file:
                max_width = max_resolutions["glow"][0]
                max_height = max_resolutions["glow"][1]
                break

        for alias in SPECULAR_ALIASES:
            if alias in file:
                max_width = max_resolutions["specular"][0]
                max_height = max_resolutions["specular"][1]
                break

        if max_width == 0 and max_height == 0:
            max_width = max_resolutions["diffuse"][0]
            max_height = max_resolutions["diffuse"][1]

        optimize_in_place(f"{input_folder}\\{file}", max_width, max_height)

    for folder in os.listdir(input_folder):
        if os.path.isdir(f"{input_folder}\\{folder}"):
            optimize_folder(f"{input_folder}\\{folder}", max_resolutions)

# megabytes
def find_size_of_images(input_folder):
    total_size = 0

    for file in os.listdir(input_folder):
        if os.path.splitext(file)[1] != ".vtf":
            continue

        total_size += os.path.getsize(f"{input_folder}\\{file}") / (1024 * 1024.0)
    
    for folder in os.listdir(input_folder):
        if os.path.isdir(f"{input_folder}\\{folder}"):
            total_size += find_size_of_images(f"{input_folder}\\{folder}")

    return total_size

def main():
    os.chdir(VTFCMD_PATH)

    start_size = find_size_of_images(INPUT_FOLDER)

    max_resolutions = {
        "diffuse": (2048, 2048),
        "normal": (1024, 1024),
        "glow": (1024, 1024),
        "specular": (1024, 1024)
    }

    optimize_folder(INPUT_FOLDER, max_resolutions)

    end_size = find_size_of_images(INPUT_FOLDER)

    print(f"\nOptimization complete, saved {start_size - end_size} MB")



if __name__ == "__main__":
    main()