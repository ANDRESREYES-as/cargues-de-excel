import tkinter as tk
from tkinter import filedialog, messagebox
import requests

BACKEND_URL = 'http://127.0.0.1:8000/excel/upload/'

class ExcelApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Procesador de Excel')
        self.create_widgets()

    def create_widgets(self):
        self.upload_btn = tk.Button(self.root, text='Seleccionar archivo Excel', command=self.select_file)
        self.upload_btn.pack(pady=20)
        self.result_text = tk.Text(self.root, height=15, width=60)
        self.result_text.pack(pady=10)
        self.open_pdf_3_7_btn = tk.Button(self.root, text='Abrir PDF Bodega-1', command=self.open_pdf_3_7, state=tk.DISABLED)
        self.open_pdf_3_7_btn.pack(pady=5)
        self.open_pdf_otros_btn = tk.Button(self.root, text='Abrir PDF Bodega-2', command=self.open_pdf_otros, state=tk.DISABLED)
        self.open_pdf_otros_btn.pack(pady=5)

        self.pdf_3_7_path = None
        self.pdf_otros_path = None

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('Excel Files', '*.xlsx')])
        if file_path:
            self.upload_file(file_path)

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                files = {'archivo': f}
                response = requests.post(BACKEND_URL, files=files)
            if response.status_code == 200:
                data = response.json()
                self.show_result(data)
            else:
                messagebox.showerror('Error', f'Error al procesar archivo: {response.text}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def show_result(self, data):
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, f"Consecutivo: {data.get('consecutivo')}\n")
        self.result_text.insert(tk.END, f"PDF iny=3 o 7: {data.get('pdf_3_7')}\n")
        self.result_text.insert(tk.END, f"PDF iny=otros: {data.get('pdf_otros')}\n")
        self.pdf_3_7_path = data.get('pdf_3_7')
        self.pdf_otros_path = data.get('pdf_otros')
        self.open_pdf_3_7_btn.config(state=tk.NORMAL if self.pdf_3_7_path else tk.DISABLED)
        self.open_pdf_otros_btn.config(state=tk.NORMAL if self.pdf_otros_path else tk.DISABLED)

    def open_pdf_3_7(self):
        if self.pdf_3_7_path:
            try:
                import os
                os.startfile(self.pdf_3_7_path)
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo abrir el PDF: {e}')

    def open_pdf_otros(self):
        if self.pdf_otros_path:
            try:
                import os
                os.startfile(self.pdf_otros_path)
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo abrir el PDF: {e}')

if __name__ == '__main__':
    root = tk.Tk()
    app = ExcelApp(root)
    root.mainloop()
