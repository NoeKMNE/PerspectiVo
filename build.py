import PyInstaller.__main__
import os
import shutil

# Nettoyer les builds précédentes
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

options = [
    'main_window.py',
    '--onefile',
    '--windowed',
    '--name=PerspectiVo',
    '--collect-all=PySide6',
    '--strip',
    # Exclure modules inutilisés
    '--exclude-module=tkinter',
    '--exclude-module=unittest',
    '--exclude-module=pydoc',
    '--exclude-module=doctest',
]

# Ajouter UPX si dossier existe
if os.path.exists('upx-4.2.4'):
    options.append('--upx-dir=upx-4.2.4')

PyInstaller.__main__.run(options)
print("\n✓ Exécutable créé dans dist/PerspectiVo.exe")
