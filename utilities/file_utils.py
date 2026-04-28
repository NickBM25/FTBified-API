from tkinter import filedialog
import tkinter as tk

def get_file_path():
    root = tk.Tk()
    root.withdraw()

    path = filedialog.askopenfilename(
        title="Selecione o arquivo SNBT",
        filetypes=[("SNBT files", "*.snbt"),("JSON files", "*.json"),("All files", "*.*")]
    )
    return path

def open_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content
