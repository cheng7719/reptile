import re
import sqlite3
import unicodedata
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText
import requests

DATABASE = "contacts.db"

email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
name_pattern = re.compile(r"(?<![\w@.])[\u4e00-\u9fa5]{3,}(?![\w@.])")
phone_extension_pattern = re.compile(r"電話：\d{2,4}-\d{6,8} 分機 (\d{3,5})")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )''')

def save_to_database(name: str, phone: str, email: str):

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM contacts WHERE name = ? AND phone = ? AND email = ?''', (name, phone, email))
        count = cursor.fetchone()[0]

        if count == 0:
            try:
                cursor.execute('''INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)''', (name, phone, email))
            except sqlite3.IntegrityError:
                pass

def scrape_contacts(url: str) -> list:

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.text

        names = name_pattern.findall(html_content)
        emails = email_pattern.findall(html_content)
        phone_extensions = phone_extension_pattern.findall(html_content)


        unique_names = []
        seen_names = set()
        for name in names:
            if name not in seen_names:
                unique_names.append(name)
                seen_names.add(name)

        phone_data = phone_extensions

        max_len = max(len(unique_names), len(phone_data), len(emails))
        unique_names += [''] * (max_len - len(unique_names))
        phone_data += [''] * (max_len - len(phone_data))
        emails += [''] * (max_len - len(emails))

        contacts = [(name, phone, email) for name, phone, email in zip(unique_names, phone_data, emails)]

        return contacts

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"無法抓取資料: {e}")

def get_display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "FW" else 1 for c in text)

def pad_to_width(text: str, width: int) -> str:
    current_width = get_display_width(text)
    return text + " " * (width - current_width)

def display_contacts(contacts: list, text_widget: ScrolledText):
    text_widget.config(state='normal')
    text_widget.delete("1.0", "end")

    text_widget.insert("end", f"{pad_to_width('姓名', 15)} {pad_to_width('分機', 15)} {'Email'}\n")
    text_widget.insert("end", "-" * 60 + "\n")  # 分隔線

    for name, phone, email in contacts:
        text_widget.insert("end", f"{pad_to_width(name, 15)} {pad_to_width(phone, 15)} {email}\n")

    text_widget.config(state='disabled')

def on_scrape_button_click(url_var: StringVar, text_widget: ScrolledText):
    url = url_var.get().strip()
    if not url:
        messagebox.showwarning("警告", "無法取得網頁:404")
        return
    try:
        contacts = scrape_contacts(url)
        if not contacts:
            messagebox.showwarning("警告", "未找到聯絡人資訊！")
        else:
            for name, phone, email in contacts:
                save_to_database(name, phone, email)
            display_contacts(contacts, text_widget)
            messagebox.showinfo("成功", "抓取完成！")
    except RuntimeError as e:
        messagebox.showerror("錯誤", str(e))

def create_app():
    root = Tk()
    root.title("聯絡資訊爬蟲程式")
    root.geometry("640x480")
    root.minsize(640, 480)

    url_label = Label(root, text="URL:")
    url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    url_var = StringVar()
    url_entry = Entry(root, textvariable=url_var)
    url_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    scrape_button = Button(root, text="抓取", command=lambda: on_scrape_button_click(url_var, text_widget))
    scrape_button.grid(row=0, column=4, padx=5, pady=5)

    text_widget = ScrolledText(root, wrap="word", state='disabled')
    text_widget.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)

    root.mainloop()

if __name__ == "__main__":
    setup_database()
    create_app()
