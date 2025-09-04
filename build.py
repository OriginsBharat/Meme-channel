import PyInstaller.__main__
import os
import shutil

if __name__ == '__main__':
    print("--- Starting PyInstaller Build ---")

    # Get the absolute path to the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spec_file = os.path.join(script_dir, 'meme_compiler.spec')

    if not os.path.exists(spec_file):
        print(f"ERROR: Spec file not found at {spec_file}")
        exit()

    # Run PyInstaller
    PyInstaller.__main__.run([
        spec_file,
        '--noconfirm',  # Overwrite the output directory without asking
        '--clean'       # Clean PyInstaller cache and remove temporary files before building
    ])

    print("\n--- PyInstaller Build Finished ---")

    # Optional: Clean up the .spec file after build
    # os.remove(spec_file)

    # The output will be in the 'dist' directory.
    print(f"Executable created in the '{os.path.abspath('dist')}' directory.")
