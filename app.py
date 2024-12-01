import re
import sqlite3
import unicodedata
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText
import requests

DATABASE = "contacts.db"

name_pattern = re.compile(r'<a[^>]*class="member_name"[^>]*>(.*?)</a>')
phone_pattern = re.compile(r'\+?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}')
email_pattern = re.compile(r'\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5,la;q=0.4',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': '_ga_SNR7NPLEYG=GS1.1.1651249603.1.0.1651250646.0; _ga_BGEHGPV3SB=GS1.1.1707539001.1.1.1707539323.0.0.0; _gid=GA1.3.1607128698.1707801742; _ga=GA1.1.381372473.1651249604; _ga_Q0EL30K2K5=GS1.1.1707801741.1.0.1707801770.0.0.0; _ga_54MVLT2EZN=GS1.1.1707843944.5.1.1707843969.0.0.0; __RequestVerificationToken_L05ldFNlcnZpY2Vz0=MrnqY4BqFXwyAR3uGWq5prQZPEwGWyzIJgIpuGFLyP8hqJ6eLKM9EWlC8NVA4MZqmyjtxmWT-9ZtzrO04NCTXcM_njimY7J0_WFWHlyWtzE1',
    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}


proxies = {
    "https": "3.70.191.255:8090",
}

def setup_database():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                iid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')

def save_to_database(name: str, phone: str, email: str):
    """
    儲存聯絡人資料到資料庫，避免重複資料。
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO contacts (name, phone, email)
                VALUES (?, ?, ?)
            ''', (name, phone, email))
        except sqlite3.IntegrityError:
            pass

def scrape_contacts(url: str) -> list:
    """
    從指定的 URL 擷取聯絡人資料。
    """
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()

        emails = email_pattern.findall(response.text)
        names = name_pattern.findall(response.text)
        phones = phone_pattern.findall(response.text)

        phones += [''] * (len(names) - len(phones))

        contacts = [(name, phone, email) for name, phone, email in zip(names, phones, emails)]
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
    for name, phone, email in contacts:
        text_widget.insert("end", f"姓名: {pad_to_width(name, 15)}\n")
        text_widget.insert("end", f"電話: {pad_to_width(phone, 15)}\n")
        text_widget.insert("end", f"Email: {email}\n\n")
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

    # URL 輸入框
    url_label = Label(root, text="URL:")
    url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    url_var = StringVar()
    url_entry = Entry(root, textvariable=url_var)
    url_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    scrape_button = Button(root, text="抓取", command=lambda: on_scrape_button_click(url_var, text_widget))
    scrape_button.grid(row=0, column=4, padx=5, pady=5)

    # 聯絡人顯示區域
    text_widget = ScrolledText(root, wrap="word", state='disabled')
    text_widget.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")

    # 權重配置
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)

    root.mainloop()

if __name__ == "__main__":
    setup_database()
    create_app()
