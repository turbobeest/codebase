""" Codebase and Codemap Extractor

This script is designed to create a comprehensive snapshot of a 
software project for visibility with Large Language Model (LLM) 
development support with codebases. It analyzes a specified directory, 
generates a detailed codemap and extracts the codebase to a single 
directory (absent any subdirectories). The tool also examines and 
documents imported libraries, providing insights into the project's 
dependencies and produces codebases and codemaps of each library 
(default is none).

Key features include:

List of ignored file types and directories to exclude from analysis
Generation of hierarchical codemap showing the project structure
Extraction of the codebase with timestamps
Analysis and documentation of imported libraries

By capturing the essence of a project's structure, contents, and 
dependencies, this tool creates a rich dataset ideal for informing 
LLMs to understand and work with complex software projects. It 
aims to enhance an LLM's ability to comprehend code organization, 
dependencies, and project architectures"""

import os
import json
import shutil
from datetime import datetime
import pkg_resources
import importlib.util
import fnmatch
from collections import defaultdict

CONFIG_FILE = "config.json"
IGNORED_PATTERNS_FILE = "ignored_patterns.txt"

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as file:
                content = file.read().strip()
                if content:
                    config = json.loads(content)
                else:
                    print("Config file is empty. Creating a new configuration.")
        except json.JSONDecodeError:
            print("Error reading config file. Creating a new configuration.")
    else:
        print("Config file not found. Creating a new configuration.")
    
    # Load ignored patterns
    ignored_extensions = set()
    ignored_folders = set()
    if os.path.exists(IGNORED_PATTERNS_FILE):
        with open(IGNORED_PATTERNS_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('.'):
                        ignored_extensions.add(line)
                    else:
                        ignored_folders.add(line)
    
    # Convert lists back to sets if they exist in the loaded config
    config['ignored_extensions'] = set(config.get('ignored_extensions', [])) | ignored_extensions
    config['ignored_folders'] = set(config.get('ignored_folders', [])) | ignored_folders
    return config

def save_config(config):
    serializable_config = {
        key: list(value) if isinstance(value, set) else value
        for key, value in config.items()
    }
    try:
        with open(CONFIG_FILE, 'w') as file:
            json.dump(serializable_config, file, indent=4)
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")

def get_file_types(directory, ignored_extensions, ignored_folders):
    file_types = set()
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(os.path.join(root, d), pattern) for pattern in ignored_folders)]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext and ext not in ignored_extensions:
                file_types.add(ext)
    return sorted(file_types)

def get_imported_libraries(directory):
    libraries = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        for line in f:
                            if line.startswith('import ') or line.startswith('from '):
                                parts = line.split()
                                if parts[0] == 'import':
                                    libraries.add(parts[1].split('.')[0])
                                elif parts[0] == 'from':
                                    libraries.add(parts[1].split('.')[0])
                    except:
                        pass
    return sorted(libraries)

def write_codemap(file, directory, indent_level=0, ignored_extensions=set(), ignored_folders=set()):
    items = os.listdir(directory)
    for item in sorted(items):
        item_path = os.path.join(directory, item)
        if any(fnmatch.fnmatch(item_path, pattern) for pattern in ignored_folders):
            continue
        indent = "│   " * indent_level + "├── "
        if os.path.isdir(item_path):
            file.write(f"{indent}{item}/\n")
            write_codemap(file, item_path, indent_level + 1, ignored_extensions, ignored_folders)
        else:
            _, ext = os.path.splitext(item)
            if ext not in ignored_extensions:
                file.write(f"{indent}{item}\n")

def copy_files(src, dest, base_directory, file_types, ignored_extensions, ignored_folders):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(os.path.join(root, d), pattern) for pattern in ignored_folders)]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in ignored_extensions or ext not in file_types:
                continue
            s = os.path.join(root, file)
            relative_path = os.path.relpath(s, base_directory)
            filename = relative_path.replace(os.path.sep, '-')
            d = os.path.join(dest, filename)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            try:
                with open(s, 'r', encoding='utf-8') as f_src:
                    content = f_src.read()
                with open(d, 'w', encoding='utf-8') as f_dest:
                    timestamp = datetime.now().strftime("# file updated %Y.%m.%d_%H:%M:%S\n")
                    f_dest.write(timestamp + content)
            except UnicodeDecodeError:
                shutil.copy2(s, d)
            except Exception as e:
                print(f"Error copying file {s}: {str(e)}")

def get_library_version(library):
    try:
        return pkg_resources.get_distribution(library).version
    except pkg_resources.DistributionNotFound:
        try:
            module = importlib.import_module(library)
            return getattr(module, '__version__', 'Unknown')
        except ImportError:
            return 'Unknown'

def get_library_info(library_name):
    spec = importlib.util.find_spec(library_name)
    if spec is None or spec.origin is None:
        return None
    
    library_dir = os.path.dirname(spec.origin)
    file_count = sum([len(files) for r, d, files in os.walk(library_dir)])
    total_size = sum(os.path.getsize(os.path.join(dirpath,filename)) 
                     for dirpath, dirnames, filenames in os.walk(library_dir) 
                     for filename in filenames)

    return {
        'path': library_dir,
        'file_count': file_count,
        'total_size': total_size
    }

def write_library_info(file, library_name, library_info):
    version = get_library_version(library_name)
    file.write(f"{library_name} (v{version})\n")
    file.write(f"Path: {library_info['path']}\n")
    file.write(f"Number of files: {library_info['file_count']}\n")
    file.write(f"Total size: {library_info['total_size'] // 1024} KB\n")
    file.write("\n" + "*" * 50 + "\n\n")

def main():
    config = load_config()
    ignored_extensions = config['ignored_extensions']
    ignored_folders = config['ignored_folders']

    selected_directory = input(f"Enter the application's root directory to analyze [{config.get('last_directory', '')}]: ").strip() or config.get('last_directory', '')
    output_directory = input(f"Enter the output directory [{config.get('last_output_directory', '')}]: ").strip() or config.get('last_output_directory', '')

    print("\nAnalyzing directory structure. This may take a bit for large codebases...")

    all_file_types = get_file_types(selected_directory, ignored_extensions, ignored_folders)
    all_libraries = get_imported_libraries(selected_directory)

    print("\nAvailable file types:")
    for i, ft in enumerate(all_file_types, 1):
        print(f"{i}. {ft}")
    file_types_input = input("Enter numbers of file types to include (comma-separated, or press Enter for all): ").strip().lower()
    if file_types_input:
        file_types = [all_file_types[int(x.strip()) - 1] for x in file_types_input.split(',')]
    else:
        file_types = all_file_types

    print("\nDetected libraries:")
    for i, lib in enumerate(all_libraries, 1):
        print(f"{i}. {lib}")
    libraries_input = input("Enter names or numbers of libraries to include (comma-separated, 'all' for all, or press Enter to exclude all): ").strip().lower()
    if libraries_input == 'all':
        libraries = all_libraries
    elif libraries_input:
        if libraries_input[0].isdigit():
            libraries = [all_libraries[int(x.strip()) - 1] for x in libraries_input.split(',')]
        else:
            libraries = [lib.strip() for lib in libraries_input.split(',')]
    else:
        libraries = []

    timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    top_level_dir = os.path.join(output_directory, os.path.basename(selected_directory))
    codebase_dir = os.path.join(top_level_dir, f"codebase-{timestamp}")
    libraries_dir = os.path.join(top_level_dir, "Libraries")

    os.makedirs(codebase_dir, exist_ok=True)
    os.makedirs(libraries_dir, exist_ok=True)

    codemap_file = os.path.join(codebase_dir, f"{os.path.basename(selected_directory)}-codemap.txt")
    with open(codemap_file, 'w', encoding='utf-8') as codemap:
        write_codemap(codemap, selected_directory, ignored_extensions=ignored_extensions, ignored_folders=ignored_folders)
        codemap.write("\nIncluded Libraries:\n")
        for lib in libraries:
            version = get_library_version(lib)
            codemap.write(f"{lib} (v{version})\n")

    copy_files(selected_directory, codebase_dir, selected_directory, file_types, ignored_extensions, ignored_folders)

    for library in libraries:
        library_info = get_library_info(library)
        if library_info:
            version = get_library_version(library)
            library_file = os.path.join(libraries_dir, f"{library}(v{version}){timestamp}.txt")
            with open(library_file, 'w', encoding='utf-8') as lib_file:
                write_library_info(lib_file, library, library_info)

    print("Operation completed successfully.")

    config['last_directory'] = selected_directory
    config['last_output_directory'] = output_directory
    save_config(config)

if __name__ == "__main__":
    main()