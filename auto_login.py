from tkinter import *
import queries, requests, time, os
import pyautogui as pg
import pyperclip as pc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cryptography.fernet import Fernet

RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

KEY_FILE_PATH = input(f"{RED}[WARN] If you don't have a key, please enter one with a name like: C:\secret.key\n[?] Enter the path of the key file: {RESET}")

def load_or_generate_key():
    if os.path.exists(KEY_FILE_PATH):
        with open(KEY_FILE_PATH, "rb") as key_file:
            return key_file.read()
    else:
        new_key = Fernet.generate_key()
        with open(KEY_FILE_PATH, "wb") as key_file:
            key_file.write(new_key)
            print(f"{GREEN}[INFO] Key is generated at: {KEY_FILE_PATH}. Keep it safe!{RESET}")
        return new_key

key = load_or_generate_key()

def encrypt_data(data, key):
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data, key):
    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
    return decrypted_data

def send_data_to_queries():

    original_url = loginUrlEntry_db.get()
    encrypted_url = encrypt_data(original_url, key)

    original_username = usernameEntry_db.get()
    encrypted_username = encrypt_data(original_username, key)

    original_password = passwordEntry_db.get()
    encrypted_password = encrypt_data(original_password, key)
    encrypted_url_str = encrypted_url.decode()
    encrypted_username_str = encrypted_username.decode()
    encrypted_password_str = encrypted_password.decode()
    
    queries.addRecord(encrypted_url_str, encrypted_username_str, encrypted_password_str)
    

def close_window():
    root.destroy()

def refreshListbox():
    list_of_records.delete(0, END)
    showRecords = queries.showRecords()
    for rowRecords in enumerate(showRecords, 1):
	    list_of_records.insert(END, rowRecords)

def delete_selected_item():
    selected_item_index = list_of_records.curselection()
    if selected_item_index:
        selected_item = list_of_records.get(selected_item_index)
        queries.deleteRecord(selected_item[1][0])

def login():
    selected_item_index = list_of_records.curselection()
    if selected_item_index:
        
        selected_item = list_of_records.get(selected_item_index)
        encrypted_url_str = selected_item[1][0]
        encrypted_username_str = selected_item[1][1]
        encrypted_password_str = selected_item[1][2]
        
        decrypted_url = decrypt_data(encrypted_url_str, key)
        decrypted_username = decrypt_data(encrypted_username_str, key)
        decrypted_password = decrypt_data(encrypted_password_str, key)

        userAgent = {'user-agent': 'CHANGE ME'}
        requests.get(decrypted_url, headers=userAgent)
        time.sleep(1)
        brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"  # Brave tarayıcının dosya yolu

        chrome_options = Options()
        chrome_options.binary_location = brave_path
        chrome_options.add_argument("--incognito")
        
        with webdriver.Chrome(options=chrome_options) as driver:
            driver.get(decrypted_url)
            time.sleep(5)
            pc.copy(decrypted_username)
            pg.hotkey("ctrl", "v")
            pg.hotkey("TAB")
            time.sleep(1)
            pc.copy(decrypted_password)
            pg.hotkey("ctrl", "v")
            pg.press("Enter")
            pc.copy("")
            close_window()

            exit_command = input(f"{GREEN}[INFO] Type 'exit' to quit: {RESET}")
            
            if exit_command.lower() == 'exit':
                driver.close()

root = Tk()
root.geometry("1000x700")
root.title("Cyber Worm - Auto Login")
root.configure(bg="#005b96")


addDatabaseFrame = LabelFrame(root, text="Add a website.", fg="red", bg="#005b96", font=('Arial', 15, 'bold'), height=300, width=950)
addDatabaseFrame.place(relx=0.01, rely=0.01)

loginUrlLabel_db = Label(addDatabaseFrame, text="Login Page URL:", bg="#005b96", fg="white", font=('Arial', 14, 'bold'))
loginUrlLabel_db.place(relx=0.3, rely=0.1)

loginUrlEntry_db = Entry(addDatabaseFrame, width=30, border=5)
loginUrlEntry_db.place(relx=0.5, rely=0.1)

usernameLabel_db = Label(addDatabaseFrame, text="Username:", bg="#005b96", fg="white", font=('Arial', 14, 'bold'))
usernameLabel_db.place(relx=0.3, rely=0.3)

usernameEntry_db = Entry(addDatabaseFrame, width=30, border=5)
usernameEntry_db.place(relx=0.5, rely=0.3)

passwordLabel_db = Label(addDatabaseFrame, text="Password:", bg="#005b96", fg="white", font=('Arial', 14, 'bold'))
passwordLabel_db.place(relx=0.3, rely=0.5)

passwordEntry_db = Entry(addDatabaseFrame, width=30, border=5)
passwordEntry_db.place(relx=0.5, rely=0.5)

add_to_Database_Button = Button(addDatabaseFrame, text="Add to Database", fg="#005b96", font=('Arial', 14, 'bold'), width=35, height=2, command=send_data_to_queries)
add_to_Database_Button.place(relx=0.05, rely=0.75)

showRecordsFrame = LabelFrame(root, text="Records.", fg="red", bg="#005b96", font=('Arial', 15, 'bold'), height=300, width=920)
showRecordsFrame.place(relx=0.01, rely=0.5)

scrbar = Scrollbar(showRecordsFrame)
scrbar.pack(side=RIGHT, fill=Y)
list_of_records = Listbox(showRecordsFrame, yscrollcommand=scrbar.set, width=85, height=10, bg='#005b96', fg='white', font=('Arial', 15, 'bold'))
list_of_records.pack(side=LEFT)
scrbar.config(command=list_of_records.yview)

goButton = Button(root, text="Go to selected website.", fg="#005b96", font=('Arial', 14, 'bold'), width=35, height=2, command=login)
goButton.place(relx=0.5, rely=0.91)

refreshButton = Button(root, text="Refresh", fg="#005b96", font=('Arial', 14, 'bold'), width=35, height=2, command=refreshListbox)
refreshButton.place(relx=0.05, rely=0.91)

delete_from_Database_Button = Button(addDatabaseFrame, text="Delete from Database", fg="#005b96", font=('Arial', 14, 'bold'), width=35, height=2, command=delete_selected_item)
delete_from_Database_Button.place(relx=0.5, rely=0.75)

refreshListbox()
root.mainloop()
