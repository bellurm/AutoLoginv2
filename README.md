# AutoLoginv2

A Python desktop credential vault and browser login automation utility built with Tkinter, SQLite, Fernet encryption, and Selenium WebDriver.

AutoLoginv2 stores website credentials locally in encrypted form and can automatically open a selected login page, locate the configured form fields, enter the credentials, and submit the login form.

The project is intended for personal automation, browser automation practice, and learning secure local credential storage concepts.

---

## Features

- Local SQLite credential storage
- Fernet encryption
- Encrypted URLs
- Encrypted usernames
- Encrypted passwords
- Automatically generated encryption key
- Tkinter desktop interface
- Selenium browser automation
- Chrome support
- Firefox support
- Microsoft Edge support
- Per-site CSS selectors
- Automatic login form filling
- Automatic form submission
- Configurable browser executable
- HTTP/HTTPS URL validation
- Parameterized SQLite queries
- Existing database schema migration
- No clipboard-based credential handling
- No PyAutoGUI keyboard automation
- No hardcoded browser path
- No hardcoded User-Agent

---

## Project Structure

```text
AutoLoginv2/
├── auto_login.py
├── queries.py
├── records.db
└── README.md
```

### `auto_login.py`

Main application.

Responsible for:

- Tkinter GUI
- Encryption and decryption
- Encryption key management
- Input validation
- Stored-record display
- Selenium browser sessions
- Login form automation
- CSS selector handling

### `queries.py`

SQLite data layer.

Responsible for:

- Database initialization
- Schema upgrades
- Record insertion
- Record retrieval
- Record deletion
- Parameterized SQL queries

---

## Requirements

Python 3.10 or newer is recommended.

Install the required Python packages:

```bash
pip install cryptography selenium
```

Tkinter is included with many Python installations.

On Debian or Ubuntu systems it may need to be installed separately:

```bash
sudo apt install python3-tk
```

A supported web browser is also required.

---

## Running AutoLoginv2

Start the application:

```bash
python3 auto_login.py
```

Default browser:

```text
Chrome
```

---

## Browser Selection

Use Firefox:

```bash
python3 auto_login.py \
    --browser firefox
```

Use Microsoft Edge:

```bash
python3 auto_login.py \
    --browser edge
```

Use Chrome:

```bash
python3 auto_login.py \
    --browser chrome
```

---

## Custom Browser Binary

A custom browser executable can be supplied with:

```bash
python3 auto_login.py \
    --browser chrome \
    --browser-binary "/path/to/browser"
```

Compatibility depends on the selected browser and WebDriver.

---

## Credential Storage

AutoLoginv2 stores:

```text
Label
Login URL
Username
Password
Username CSS selector
Password CSS selector
Submit CSS selector
```

The following values are encrypted before being stored:

```text
URL
Username
Password
```

CSS selectors and labels are not treated as secrets.

---

## Default Data Location

Credential data is stored outside the Git repository by default.

### Windows

```text
%LOCALAPPDATA%\AutoLoginv2\
```

### Linux

```text
~/.local/share/autologinv2/
```

### macOS

```text
~/Library/Application Support/AutoLoginv2/
```

The directory contains:

```text
records.db
autologin.key
```

---

## Custom Database

Use another SQLite database:

```bash
python3 auto_login.py \
    --db-file /path/to/records.db
```

Example using the repository's historical database:

```bash
python3 auto_login.py \
    --db-file ./records.db
```

---

## Custom Encryption Key

Use another Fernet key:

```bash
python3 auto_login.py \
    --key-file /secure/location/autologin.key
```

The same key must be used to decrypt records that were encrypted with it.

Losing the key means losing access to the encrypted credentials.

---

## Adding a Website

The GUI contains the following fields:

```text
Label
Login URL
Username
Password
Username CSS selector
Password CSS selector
Submit CSS selector
```

Example:

```text
Label:
Example

Login URL:
https://example.com/login

Username:
user@example.com

Password:
********
```

Click:

```text
Add Record
```

to encrypt and store the record.

---

## CSS Selectors

Websites use different HTML structures for login forms.

AutoLoginv2 therefore stores CSS selectors for each website.

Default username selector:

```css
input[name='username'],
input[name='email'],
input[type='email'],
input[autocomplete='username'],
input[type='text']
```

Default password selector:

```css
input[name='password'],
input[type='password'],
input[autocomplete='current-password']
```

Default submit selector:

```css
button[type='submit'],
input[type='submit']
```

These defaults work with many conventional login forms, but some websites require custom selectors.

---

## Finding a CSS Selector

Open the login page in your browser.

Use the browser developer tools to inspect the username, password, and submit elements.

Example HTML:

```html
<input id="login-user" type="email">
<input id="login-password" type="password">
<button id="login-submit">Login</button>
```

Corresponding CSS selectors:

```text
Username:
#login-user

Password:
#login-password

Submit:
#login-submit
```

Store those selectors with the credential record.

---

## Login Workflow

Select a record and click:

```text
Open & Login
```

AutoLoginv2 performs:

```text
Selected Record
      │
      ▼
Decrypt URL
      │
      ▼
Decrypt Username
      │
      ▼
Decrypt Password
      │
      ▼
Start Selenium WebDriver
      │
      ▼
Open Login Page
      │
      ▼
Wait for Username Field
      │
      ▼
Enter Username
      │
      ▼
Wait for Password Field
      │
      ▼
Enter Password
      │
      ▼
Find Submit Button
      │
      ▼
Submit Login
```

If no submit selector is configured, AutoLoginv2 sends:

```text
ENTER
```

from the password field.

---

## Why CSS Selectors?

The original implementation relied on:

```text
Clipboard
PyAutoGUI
TAB key
Keyboard simulation
```

That approach depended heavily on:

- Window focus
- Browser layout
- Tab order
- Timing
- Clipboard state

AutoLoginv2 now interacts directly with browser DOM elements through Selenium.

Each site can therefore define the exact form elements that should receive credentials.

---

## Encryption

AutoLoginv2 uses:

```text
cryptography.fernet.Fernet
```

for credential encryption.

Before storage:

```text
Plaintext URL
Plaintext Username
Plaintext Password
        │
        ▼
      Fernet
        │
        ▼
Encrypted SQLite values
```

During login:

```text
Encrypted SQLite values
        │
        ▼
      Fernet
        │
        ▼
Temporary plaintext values
        │
        ▼
Selenium WebDriver
```

---

## Encryption Key

If no key exists, AutoLoginv2 generates one automatically.

The default key filename is:

```text
autologin.key
```

On Unix-like operating systems the application attempts to restrict its permissions to:

```text
600
```

Do not publish or share this key.

Anyone with both the database and encryption key can decrypt the stored credentials.

---

## Database Security

SQLite queries use parameter binding rather than manually constructing SQL statements.

Conceptually:

```python
cursor.execute(
    "DELETE FROM siteRecords WHERE rowid = ?",
    (record_id,),
)
```

This keeps database values separate from SQL syntax.

---

## Database Compatibility

The original AutoLoginv2 database used:

```text
url
username
passwd
```

The new data layer keeps the original table and automatically adds:

```text
label
username_selector
password_selector
submit_selector
```

Existing records are therefore not intentionally deleted during initialization.

Old encrypted records still require their original Fernet key.

---

## Browser Drivers

AutoLoginv2 uses Selenium WebDriver.

Modern Selenium releases include Selenium Manager, which can automatically manage browser drivers when an appropriate driver is not already available.

An internet connection may be required the first time Selenium needs to obtain a compatible driver.

---

## Security Improvements

Compared with the original implementation, AutoLoginv2 no longer:

- Copies usernames to the system clipboard
- Copies passwords to the system clipboard
- Uses PyAutoGUI to press TAB
- Uses PyAutoGUI to press ENTER
- Requires a hardcoded Brave installation path
- Performs an unnecessary HTTP request before browser launch
- Uses a hardcoded User-Agent
- Builds SQL statements with string interpolation
- Requires entering the key path interactively on every startup

---

## Security Limitations

AutoLoginv2 is an educational personal credential utility and should not be considered a replacement for a mature password manager.

Important limitations include:

- The encryption key is stored locally.
- A compromised operating-system account may gain access to both the database and key.
- Credentials exist in application memory while being used.
- Selenium sends credentials into the website's login form.
- Browser extensions or malware may compromise credentials independently of AutoLoginv2.
- The project does not provide a master-password-derived key.
- The project does not provide hardware-backed key storage.
- The project does not provide cloud synchronization.
- The project does not implement MFA/TOTP storage.

For high-value credentials, use a dedicated and professionally audited password manager.

---

## Website Compatibility

Not every login page can be automated with a simple username/password form.

Websites may use:

- Multi-step login flows
- CAPTCHAs
- MFA
- Passkeys
- JavaScript-controlled forms
- iframes
- Shadow DOM
- Anti-automation mechanisms
- SSO providers

AutoLoginv2 intentionally does not attempt to bypass these protections.

Custom CSS selectors can improve compatibility with conventional login forms.

---

## What This Project Demonstrates

AutoLoginv2 demonstrates practical experience with:

- Python
- Tkinter
- SQLite
- Cryptography
- Fernet
- Selenium WebDriver
- Browser automation
- CSS selectors
- Local credential storage
- Input validation
- Parameterized SQL
- Cross-platform application paths
- GUI development
- Security-conscious automation

---

## Responsible Use

Only automate logins for accounts and services that you are authorized to access.

Do not use this project to access third-party accounts or systems without permission.

---

## Author

**Cyber Worm**

GitHub: [@bellurm](https://github.com/bellurm)
