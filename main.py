"""
Point d'entrée principal de l'application MK-St_Venant.
Lancement de l'interface graphique CustomTkinter.
"""

import sys
import os

# Ajout du répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import MainApplication


def resource_path(relative_path: str) -> str:
    """Retourne un chemin absolu vers une ressource, compatible exécution source et PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def main():
    try:
        app = MainApplication()
        icon_candidates = [
            resource_path(os.path.join("assets", "mk-st-venant-icon.ico")),
            resource_path(os.path.join("assets", "mk-st-venant-icon.png")),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "mk-st-venant-icon.ico"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "mk-st-venant-icon.png"),
        ]
        for icon_path in icon_candidates:
            if not os.path.exists(icon_path):
                continue
            try:
                if icon_path.lower().endswith(".ico"):
                    app.iconbitmap(icon_path)
                else:
                    import tkinter as tk
                    icon_img = tk.PhotoImage(file=icon_path)
                    app.iconphoto(True, icon_img)
                    app._icon_img_ref = icon_img  # éviter garbage collection
                break
            except Exception:
                continue
        app.mainloop()
    except Exception as e:
        print(f"Erreur lors de l'exécution de MK-St_Venant : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
