import re
import sqlite3
import unicodedata
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText
import requests

DATABASE = "contacts.db"

email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
name_pattern = re.compile(r"(?<![\w@.])[\u4e00-\u9fa5]{3,}(?![\w@.])")
title_pattern = re.compile(r"職稱：([^<]+)")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )''')

def save_to_database(name: str, title: str, email: str):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM contacts WHERE name = ? AND title = ? AND email = ?''', (name, title, email))
        count = cursor.fetchone()[0]

        if count == 0:
            try:
                cursor.execute('''INSERT INTO contacts (name, title, email) VALUES (?, ?, ?)''', (name, title, email))
            except sqlite3.IntegrityError:
                pass

def scrape_contacts(url: str) -> list:
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.text

        teacher_pattern = r'<div class="member_name">.*?<a href=".*?">([^<]+)</a>.*?<span>(.*?)</span>.*?<div class="member_info_title">.*?職稱</div>.*?<div class="member_info_content">([^<]+)</div>.*?<div class="member_info_title">.*?學歷</div>.*?<div class="member_info_content">([^<]+)</div>.*?<div class="member_info_title">.*?信箱</div>.*?<div class="member_info_content">.*?mailto:(.*?)</a>.*?'

        teachers = re.findall(teacher_pattern, html_content, re.DOTALL)

        contacts = []
        for teacher in teachers:
            name_chinese = teacher[0].strip()
            title = teacher[2].strip()
            email_raw = teacher[4].strip()

            email = email_raw.split('"')[0].replace("//", "")

            contacts.append((name_chinese, title, email))

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

    text_widget.insert("end", f"{pad_to_width('姓名', 15)} {pad_to_width('職稱', 30)} {'Email'}\n")
    text_widget.insert("end", "-" * 80 + "\n")

    for name, title, email in contacts:
        text_widget.insert("end", f"{pad_to_width(name, 15)} {pad_to_width(title, 30)} {email}\n")

    text_widget.config(state='disabled')

def on_scrape_button_click(url_var: StringVar, text_widget: ScrolledText):
    url = url_var.get().strip()
    if not url:
        messagebox.showwarning("警告", "無法取得網頁: 404")
        return
    try:
        contacts = scrape_contacts(url)
        if not contacts:
            messagebox.showwarning("警告", "未找到聯絡人資訊！")
        else:
            for name, title, email in contacts:
                save_to_database(name, title, email)
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
