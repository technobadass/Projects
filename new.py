import customtkinter as ctk
from PIL import Image, ImageTk
import os
import mysql.connector
from model import get_caption_model, generate_caption
import requests
from io import BytesIO
import tensorflow as tf
from tkinter import messagebox, filedialog  # Fixed import issue
import base64 
import pyttsx3
import pyperclip  # Import for clipboard functionality
from googletrans import Translator
from gtts import gTTS
import io
import pygame
from google.cloud import texttospeech



engine = pyttsx3.init()
# Check TensorFlow installation
try:
    print(f"TensorFlow Version: {tf.__version__}")
except Exception as e:
    print(f"Error loading TensorFlow: {e}")

# MySQL connection function
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="sem6",
        port=3307
    )

class LoginSignupApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Login or Sign Up")
        self.window.geometry("400x400")
        self.create_login_page()

    def create_login_page(self):
        for widget in self.window.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.window, text="Login", font=("Arial", 24))
        title.pack(pady=20)

        username_label = ctk.CTkLabel(self.window, text="Username:")
        username_label.pack(pady=5)
        self.username_entry = ctk.CTkEntry(self.window)
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self.window, text="Password:")
        password_label.pack(pady=5)
        self.password_entry = ctk.CTkEntry(self.window, show="*")
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self.window, text="Login", command=self.login)
        login_button.pack(pady=10)

        switch_to_signup = ctk.CTkButton(self.window, text="Create New Account", command=self.create_signup_page)
        switch_to_signup.pack(pady=10)

        self.message_label = ctk.CTkLabel(self.window, text="")
        self.message_label.pack(pady=10)

    def create_signup_page(self):
        for widget in self.window.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.window, text="Sign Up", font=("Arial", 24))
        title.pack(pady=20)

        username_label = ctk.CTkLabel(self.window, text="Username:")
        username_label.pack(pady=5)
        self.username_entry = ctk.CTkEntry(self.window)
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self.window, text="Password:")
        password_label.pack(pady=5)
        self.password_entry = ctk.CTkEntry(self.window, show="*")
        self.password_entry.pack(pady=5)

        confirm_password_label = ctk.CTkLabel(self.window, text="Confirm Password:")
        confirm_password_label.pack(pady=5)
        self.confirm_password_entry = ctk.CTkEntry(self.window, show="*")
        self.confirm_password_entry.pack(pady=5)

        signup_button = ctk.CTkButton(self.window, text="Sign Up", command=self.signup)
        signup_button.pack(pady=10)

        switch_to_login = ctk.CTkButton(self.window, text="Already Have an Account? Login", command=self.create_login_page)
        switch_to_login.pack(pady=10)

        self.message_label = ctk.CTkLabel(self.window, text="")
        self.message_label.pack(pady=10)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Fields cannot be empty!")
            return

        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data WHERE Username = %s AND Password = %s", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                messagebox.showinfo("Success", "Login successful!")
                self.window.destroy()
                ImageCaptionerApp().run()
            else:
                messagebox.showerror("Error", "Invalid username or password!")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def signup(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()

        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "Fields cannot be empty!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO data (Username, Password) VALUES (%s, %s)", (username, password))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Sign-up successful! Please log in.")
            self.create_login_page()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def run(self):
        engine.runAndWait()
        self.window.mainloop()

class ImageCaptionerApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Image Captioner")
        self.window.geometry("800x600")
        
        self.caption_model = get_caption_model()
        self.translator = Translator()  # Initialize Translator
        # Add a new instance variable in __init__
        self.translated_text = ""
        self.create_widgets()

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

         # Update background color when mode changes
        self.update_translated_caption_colors()  # Apply color changes


    def update_translated_caption_colors(self):
        text_color, bg_color = self.get_theme_colors()
        self.translated_caption_label.configure(text_color=text_color, fg_color=bg_color)
        
    def create_widgets(self):
        title = ctk.CTkLabel(self.window, text="Image Captioner", font=("Arial", 24))
        title.pack(pady=20)
        # Dropdown for selecting language (Added Marathi & Japanese)
        self.language_options = {
            "English": "en",
            "French": "fr",
            "Spanish": "es",
            "German": "de",
            "Hindi": "hi",
            "Marathi": "mr",
            "Japanese": "ja"
        }

        self.theme_switch = ctk.CTkSwitch(self.window, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(pady=5)

        url_frame = ctk.CTkFrame(self.window)
        url_frame.pack(pady=10, padx=20, fill="x")

        url_label = ctk.CTkLabel(url_frame, text="Enter Image URL:")
        url_label.pack(side="left", padx=5)

        self.url_entry = ctk.CTkEntry(url_frame, width=400)
        self.url_entry.pack(side="left", padx=5)

        url_button = ctk.CTkButton(url_frame, text="Load Image", command=self.load_from_url)
        url_button.pack(side="left", padx=5)

        upload_button = ctk.CTkButton(self.window, text="Upload Image", command=self.load_from_file)
        upload_button.pack(pady=10)

        self.image_label = ctk.CTkLabel(self.window, text="")
        self.image_label.pack(pady=10)

        self.caption_label = ctk.CTkLabel(self.window, text="", font=("Arial", 16))
        self.caption_label.pack(pady=10)

        self.translated_caption_label = ctk.CTkLabel(self.window, text="", font=("Arial", 16), fg_color="lightgrey")
        self.translated_caption_label.pack(pady=10)

        self.selected_language = ctk.StringVar(value="English")
        self.language_dropdown = ctk.CTkComboBox(self.window, values=list(self.language_options.keys()),
                                                 command=self.translate_caption, variable=self.selected_language)
        self.language_dropdown.pack(pady=10)

        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(pady=10)

        read_button = ctk.CTkButton(button_frame, text="Read", command=self.read_caption)
        read_button.pack(side="left", padx=5)

        copy_button = ctk.CTkButton(button_frame, text="Copy", command=self.copy_caption)
        copy_button.pack(side="left", padx=5)

        read_translated_button = ctk.CTkButton(button_frame, text="Read Translated", command=self.read_translated_caption)
        read_translated_button.pack(side="left", padx=5)

    def copy_caption(self):
        caption = self.caption_label.cget("text").replace("Caption: ", "")
        if caption:
            pyperclip.copy(caption)
            messagebox.showinfo("Copied", "Caption copied to clipboard!")
    def get_background_color(self):
        return "white" if ctk.get_appearance_mode() == "light" else "black"

    def load_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        try:
            if url.startswith('data:image'):
                image_data = base64.b64decode(url.split(',', 1)[1])
                img = Image.open(BytesIO(image_data))
                self.process_image(img)
            else:
                if not url.startswith(('http://', 'https://')):
                    messagebox.showerror("Error", "Invalid URL. Must start with http:// or https://")
                    return
                
                response = requests.get(url, stream=True)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                self.process_image(img)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {str(e)}")

    def load_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            img = Image.open(file_path)
            self.process_image(img)

    def process_image(self, img):
        img = img.convert('RGB')
        self.display_image(img)
        img.save('tmp.jpg')
        self.generate_captions()

    def read_caption(self):
        caption = self.caption_label.cget("text").replace("Caption: ", "")
        if caption:
            engine.say(caption)
            engine.runAndWait()
        else:
            messagebox.showwarning("Warning", "No caption available to read.")

    def display_image(self, img):
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def generate_captions(self):
        caption = generate_caption('tmp.jpg', self.caption_model)
        self.caption_label.configure(text=f"Caption: {caption}")
        self.translate_caption()

    def translate_caption(self, *args):
        caption = self.caption_label.cget("text").replace("Caption: ", "")
        target_lang = self.language_options[self.selected_language.get()]

        if caption:
            translated = self.translator.translate(caption, dest=target_lang).text
            self.translated_text = translated  # Store the translated text

            text_color, bg_color = self.get_theme_colors()
            self.translated_caption_label.configure(text=f"Translated: {translated}", text_color=text_color, fg_color=bg_color)

    def read_translated_caption(self):
        translated_text = self.translated_caption_label.cget("text").replace("Translated: ", "").strip()

        if translated_text:
            try:
                lang_code = self.language_options[self.selected_language.get()]
                
                # Use slow=True for Marathi to make it clearer
                slow_mode = True if lang_code == "mr" else False

                tts = gTTS(text=translated_text, lang=lang_code, slow=slow_mode)

                # Use an in-memory file
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                audio_data.seek(0)

                # Initialize pygame mixer
                pygame.mixer.init()
                pygame.mixer.music.load(audio_data, "mp3")
                pygame.mixer.music.play()

            except Exception as e:
                messagebox.showerror("Error", f"Could not read translated caption: {e}")
        else:
            messagebox.showwarning("Warning", "No translated caption available to read.")

    def get_theme_colors(self):
        if ctk.get_appearance_mode() == "Dark":
            return "white", "black"  # Text (White), Background (Black)
        else:
            return "black", "white"  # Text (Black), Background (White)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = LoginSignupApp()
    app.run()