import os
import subprocess
from colorama import Fore, Style, init
from PIL import Image
import argparse

# Initialize colorama for colorful console output
init(autoreset=True)

# Set the path to exiftool.exe
EXIFTOOL_PATH = r"C:\Users\block\exiftool\exiftool.exe"

def read_file(file_path):
    """Read content from a file and return lines as a list."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    return []

def list_files_in_directory(directory):
    """List files in a directory and return their names."""
    if os.path.exists(directory):
        return [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    return []

def prompt_user_to_select_file(directory):
    """Prompt the user to select a file from a directory."""
    files = list_files_in_directory(directory)
    if not files:
        return None

    print(Fore.CYAN + f"Files available in '{directory}':")
    for idx, file in enumerate(files, 1):
        print(f"[{idx}] {file}")

    while True:
        choice = input(Fore.CYAN + "Enter the number of the file to select, or '0' to skip: ").strip()
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return os.path.join(directory, files[int(choice) - 1])
        print(Fore.RED + "Invalid selection. Please try again.")

def find_images(input_dir):
    """Recursively find all images in the given directory."""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp'}
    image_files = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(tuple(valid_extensions)):
                image_files.append(os.path.join(root, file))

    return image_files

def convert_webp_to_jpg(image_files):
    """Convert all WebP images in the list to JPG format and delete the original WebP files."""
    converted_files = []
    for image_path in image_files:
        if image_path.lower().endswith('.webp'):
            try:
                img = Image.open(image_path).convert('RGB')
                new_path = image_path.rsplit('.', 1)[0] + '.jpg'
                img.save(new_path, 'JPEG')
                converted_files.append(new_path)
                os.remove(image_path)  # Delete the original WebP file
                print(Fore.GREEN + f"Converted and deleted: {image_path} -> {new_path}")
            except Exception as e:
                print(Fore.RED + f"Failed to convert {image_path}: {e}")
    return converted_files

def update_metadata(image_files, keywords, author=None, copyright_info=None, title=None, subject=None, comments=None):
    """Update metadata for images using exiftool."""
    updated_count = 0

    # Filter out deleted WebP images
    image_files = [img for img in image_files if os.path.exists(img)]

    for image in image_files:
        try:
            for keyword in keywords:
                cmd = [
                    EXIFTOOL_PATH,
                    f'-keywords-={keyword}',
                    f'-keywords+={keyword}',
                ]
                if author:
                    cmd.append(f'-author={author}')
                if copyright_info:
                    cmd.append(f'-copyright="{copyright_info}"')
                if title:
                    cmd.append(f'-title="{title}"')
                if subject:
                    cmd.append(f'-subject="{subject}"')
                if comments:
                    cmd.append(f'-comment="{comments}"')
                cmd.extend(['-overwrite_original', '-preserve', image])
                result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    updated_count += 1
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Error updating {image}: {e.stderr.decode('utf-8') if e.stderr else e}")
        except Exception as e:
            print(Fore.RED + f"Unexpected error updating {image}: {str(e)}")

    return updated_count

def main():
    # Prompt user to select files
    keyword_file = prompt_user_to_select_file('keywords')
    title_file = prompt_user_to_select_file('./title')
    copyright_file = prompt_user_to_select_file('./copyright')

    # Read selected files
    keywords = read_file(keyword_file) if keyword_file else []
    title = read_file(title_file)[0] if title_file else None
    copyright_info = read_file(copyright_file)[0] if copyright_file else None

    if not keywords:
        print(Fore.RED + "No keywords selected. Exiting.")
        return

    # Prompt user for input directory
    input_dir = input(Fore.CYAN + "Enter the directory containing images: ").strip()
    if not os.path.isdir(input_dir):
        print(Fore.RED + f"Directory '{input_dir}' does not exist.")
        return

    # Find images
    images = find_images(input_dir)
    print(Fore.YELLOW + f"Found {len(images)} images in '{input_dir}'.")

    if not images:
        print(Fore.RED + "No images found. Exiting.")
        return

    # Check for WebP images and prompt for conversion
    webp_images = [img for img in images if img.lower().endswith('.webp')]
    if webp_images:
        print(Fore.YELLOW + f"Found {len(webp_images)} WebP images.")
        convert_choice = input(Fore.CYAN + "Do you want to convert all WebP images to JPG? (y/n): ").strip().lower()
        if convert_choice == 'y':
            new_images = convert_webp_to_jpg(webp_images)
            images.extend(new_images)

    # Update metadata
    updated_count = update_metadata(images, keywords, title=title, copyright_info=copyright_info)
    print(Fore.GREEN + f"Updated metadata for {updated_count} out of {len(images)} images.")

if __name__ == "__main__":
    main()
