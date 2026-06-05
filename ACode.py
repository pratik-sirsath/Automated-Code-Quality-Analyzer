import os
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk
from dotenv import load_dotenv
import google.generativeai as genai

# Load Gemini API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
else:
    raise ValueError("Gemini API key not found. Please check your .env file.")

class CodeAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.setup_menu()
        self.setup_theme()

    def setup_window(self):
        self.root.geometry("1200x800")
        self.root.title("AI Code Analyzer Pro")
        self.root.minsize(800, 600)
        self.root.configure(bg="#e6f0fa")

    def setup_theme(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TFrame", background="#e6f0fa")
        self.style.configure("TLabel", background="#e6f0fa", foreground="#1f3a93", font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton",
                             background="#4a90e2",
                             foreground="white",
                             font=("Segoe UI", 10, "bold"),
                             padding=6,
                             relief="flat")
        self.style.map("TButton",
                       background=[('active', '#357ABD'), ('pressed', '#2d5f99')],
                       foreground=[('pressed', 'white'), ('active', 'white')])

    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        self.header_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        try:
            logo_img = Image.open("img/logo_p.png").resize((40, 40))
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(self.header_frame, image=self.logo, style="TLabel")
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logo: {e}")

        self.title_label = ttk.Label(
            self.header_frame,
            text="AI Code Analyzer Pro",
            font=("Segoe UI", 18, "bold"),
            foreground="#1f3a93"
        )
        self.title_label.pack(side=tk.LEFT)

        # Code panels
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashwidth=8)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Input panel
        self.input_frame = ttk.Frame(self.paned_window)
        self.input_label = ttk.Label(self.input_frame, text="Original Code")
        self.input_label.pack(anchor=tk.W, pady=(0, 5))

        self.textbox1 = scrolledtext.ScrolledText(
            self.input_frame,
            font=("Consolas", 11),
            wrap=tk.WORD,
            undo=True,
            padx=10,
            pady=10,
            bg="#ffffff",
            fg="#000000",
            insertbackground="#1f3a93"
        )
        self.textbox1.pack(fill=tk.BOTH, expand=True)

        # Output panel
        self.output_frame = ttk.Frame(self.paned_window)
        self.output_label = ttk.Label(self.output_frame, text="Corrected Code")
        self.output_label.pack(anchor=tk.W, pady=(0, 5))

        self.textbox2 = scrolledtext.ScrolledText(
            self.output_frame,
            font=("Consolas", 11),
            wrap=tk.WORD,
            undo=True,
            padx=10,
            pady=10,
            bg="#f9f9f9",
            fg="#000000",
            insertbackground="#1f3a93"
        )
        self.textbox2.pack(fill=tk.BOTH, expand=True)

        self.paned_window.add(self.input_frame)
        self.paned_window.add(self.output_frame)

        # Button panel
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))

        self.analyze_btn = ttk.Button(
            self.button_frame,
            text="Analyze Code",
            command=self.analysis_action
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            self.button_frame,
            text="Clear All",
            command=self.clear_all
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = ttk.Button(
            self.button_frame,
            text="Save Output",
            command=self.save_output
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            background="#d0e4ff",
            foreground="#1f3a93",
            font=("Segoe UI", 9, "italic")
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save Output", command=self.save_output)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Cut", command=self.cut_text)
        edit_menu.add_command(label="Copy", command=self.copy_text)
        edit_menu.add_command(label="Paste", command=self.paste_text)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def analysis_action(self):
        code_to_analyze = self.textbox1.get("1.0", tk.END).strip()
        if not code_to_analyze:
            messagebox.showwarning("Input Error", "Please enter code to analyze.")
            return

        self.set_status("Analyzing code...")
        self.root.config(cursor="watch")
        self.root.update()

        prompt = f"""You are an expert Python code analyzer. Please:
1. Analyze this code thoroughly
2. Identify all errors and potential issues
3. Provide a corrected version
4. Include explanations for major changes

Format response as:
```python
# Corrected code
[code here]
{code_to_analyze}
```"""

        try:
            response = model.generate_content(prompt)
            corrected_code = self.extract_code(response.text)
            self.textbox2.delete("1.0", tk.END)
            self.textbox2.insert(tk.END, corrected_code)
            self.set_status("Analysis complete")
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to analyze code:\n{e}")
            self.set_status("Analysis failed")
        finally:
            self.root.config(cursor="")

    def extract_code(self, text):
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.textbox1.delete("1.0", tk.END)
                    self.textbox1.insert(tk.END, f.read())
                self.set_status(f"Opened: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_output(self):
        content = self.textbox2.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Error", "No content to save")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.set_status(f"Saved: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def clear_all(self):
        self.textbox1.delete("1.0", tk.END)
        self.textbox2.delete("1.0", tk.END)
        self.set_status("Cleared all content")

    def cut_text(self):
        self.root.focus_get().event_generate("<<Cut>>")

    def copy_text(self):
        self.root.focus_get().event_generate("<<Copy>>")

    def paste_text(self):
        self.root.focus_get().event_generate("<<Paste>>")

    def show_about(self):
        about_msg = """AI Code Analyzer Pro\n
Version 1.0\n
Uses Google Gemini AI for advanced code analysis\n
and Black for automatic code formatting"""
        messagebox.showinfo("About", about_msg)

    def set_status(self, message):
        self.status_var.set(message)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeAnalyzerApp(root)
    root.mainloop()
