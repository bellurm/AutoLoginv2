from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    X,
    Y,
    StringVar,
    Tk,
    messagebox,
)
from tkinter import ttk
from urllib.parse import urlparse

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import (
    expected_conditions as EC,
)
from selenium.webdriver.support.ui import (
    WebDriverWait,
)

from queries import Database


APP_NAME = "AutoLoginv2"
VERSION = "3.0.0"

DEFAULT_USERNAME_SELECTOR = (
    "input[name='username'], "
    "input[name='email'], "
    "input[type='email'], "
    "input[autocomplete='username'], "
    "input[type='text']"
)

DEFAULT_PASSWORD_SELECTOR = (
    "input[name='password'], "
    "input[type='password'], "
    "input[autocomplete='current-password']"
)

DEFAULT_SUBMIT_SELECTOR = (
    "button[type='submit'], "
    "input[type='submit']"
)


def default_data_dir() -> Path:
    if os.name == "nt":
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home()
                / "AppData"
                / "Local",
            )
        )

        return base / APP_NAME

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / APP_NAME
        )

    base = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            Path.home()
            / ".local"
            / "share",
        )
    )

    return base / APP_NAME.lower()


def parse_args() -> argparse.Namespace:
    data_dir = default_data_dir()

    parser = argparse.ArgumentParser(
        description=(
            "Encrypted local credential vault "
            "with Selenium-based browser login automation."
        )
    )

    parser.add_argument(
        "--db-file",
        default=str(
            data_dir / "records.db"
        ),
        help="SQLite database path.",
    )

    parser.add_argument(
        "--key-file",
        default=str(
            data_dir / "autologin.key"
        ),
        help="Fernet key path.",
    )

    parser.add_argument(
        "--browser",
        choices=(
            "chrome",
            "firefox",
            "edge",
        ),
        default="chrome",
        help=(
            "Browser used for automation "
            "(default: chrome)."
        ),
    )

    parser.add_argument(
        "--browser-binary",
        help=(
            "Optional custom browser executable path."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args()


def load_or_create_key(
    path: Path,
) -> bytes:

    path = path.expanduser()

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if path.exists():
        key = path.read_bytes().strip()

    else:
        key = Fernet.generate_key()

        try:
            with path.open("xb") as key_file:
                key_file.write(key)

        except FileExistsError:
            key = path.read_bytes().strip()

        if os.name != "nt":
            try:
                path.chmod(0o600)
            except OSError:
                pass

    try:
        Fernet(key)

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"Invalid Fernet key file: {path}"
        ) from exc

    return key


def validate_url(
    value: str,
) -> str:

    value = value.strip()
    parsed = urlparse(value)

    if (
        parsed.scheme
        not in {
            "http",
            "https",
        }
        or not parsed.netloc
    ):
        raise ValueError(
            "URL must be a complete "
            "http:// or https:// address."
        )

    return value


class VaultCipher:
    def __init__(
        self,
        key: bytes,
    ) -> None:

        self._fernet = Fernet(key)

    def encrypt(
        self,
        value: str,
    ) -> str:

        return self._fernet.encrypt(
            value.encode()
        ).decode("ascii")

    def decrypt(
        self,
        token: str,
    ) -> str:

        try:
            return self._fernet.decrypt(
                token.encode("ascii")
            ).decode()

        except (
            InvalidToken,
            UnicodeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "This record cannot be decrypted "
                "with the current key."
            ) from exc


class AutoLoginApp:
    def __init__(
        self,
        root: Tk,
        database: Database,
        cipher: VaultCipher,
        browser: str,
        browser_binary: str | None,
        db_path: Path,
        key_path: Path,
    ) -> None:

        self.root = root
        self.database = database
        self.cipher = cipher

        self.browser = browser
        self.browser_binary = (
            browser_binary
        )

        self.drivers: list[object] = []

        self.label_var = StringVar()
        self.url_var = StringVar()
        self.username_var = StringVar()
        self.password_var = StringVar()

        self.username_selector_var = (
            StringVar(
                value=(
                    DEFAULT_USERNAME_SELECTOR
                )
            )
        )

        self.password_selector_var = (
            StringVar(
                value=(
                    DEFAULT_PASSWORD_SELECTOR
                )
            )
        )

        self.submit_selector_var = (
            StringVar(
                value=(
                    DEFAULT_SUBMIT_SELECTOR
                )
            )
        )

        self.status_var = StringVar(
            value="Ready."
        )

        self.root.title(
            f"{APP_NAME} {VERSION}"
        )

        self.root.geometry(
            "1100x700"
        )

        self.root.minsize(
            900,
            600,
        )

        self._build_ui(
            db_path,
            key_path,
        )

        self.refresh_records()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

    def _build_ui(
        self,
        db_path: Path,
        key_path: Path,
    ) -> None:

        main = ttk.Frame(
            self.root,
            padding=12,
        )

        main.pack(
            fill=BOTH,
            expand=True,
        )

        form = ttk.LabelFrame(
            main,
            text="Credential Record",
            padding=10,
        )

        form.pack(
            fill=X,
        )

        form.columnconfigure(
            1,
            weight=1,
        )

        fields = (
            (
                "Label",
                self.label_var,
                False,
            ),
            (
                "Login URL",
                self.url_var,
                False,
            ),
            (
                "Username",
                self.username_var,
                False,
            ),
            (
                "Password",
                self.password_var,
                True,
            ),
            (
                "Username CSS selector",
                self.username_selector_var,
                False,
            ),
            (
                "Password CSS selector",
                self.password_selector_var,
                False,
            ),
            (
                "Submit CSS selector",
                self.submit_selector_var,
                False,
            ),
        )

        for row, (
            label,
            variable,
            secret,
        ) in enumerate(fields):

            ttk.Label(
                form,
                text=f"{label}:",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 8),
                pady=4,
            )

            ttk.Entry(
                form,
                textvariable=variable,
                show=(
                    "*"
                    if secret
                    else ""
                ),
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4,
            )

        buttons = ttk.Frame(
            form
        )

        buttons.grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        ttk.Button(
            buttons,
            text="Add Record",
            command=self.add_record,
        ).pack(
            side=LEFT
        )

        ttk.Button(
            buttons,
            text="Clear Form",
            command=self.clear_form,
        ).pack(
            side=LEFT,
            padx=(8, 0),
        )

        records = ttk.LabelFrame(
            main,
            text="Stored Records",
            padding=10,
        )

        records.pack(
            fill=BOTH,
            expand=True,
            pady=(12, 0),
        )

        self.tree = ttk.Treeview(
            records,
            columns=(
                "label",
                "url",
                "username",
            ),
            show="headings",
            selectmode="browse",
        )

        for (
            column,
            title,
            width,
        ) in (
            (
                "label",
                "Label",
                180,
            ),
            (
                "url",
                "URL",
                450,
            ),
            (
                "username",
                "Username",
                250,
            ),
        ):
            self.tree.heading(
                column,
                text=title,
            )

            self.tree.column(
                column,
                width=width,
                anchor="w",
            )

        scrollbar = ttk.Scrollbar(
            records,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side=LEFT,
            fill=BOTH,
            expand=True,
        )

        scrollbar.pack(
            side=RIGHT,
            fill=Y,
        )

        actions = ttk.Frame(
            main
        )

        actions.pack(
            fill=X,
            pady=(10, 0),
        )

        ttk.Button(
            actions,
            text="Open & Login",
            command=(
                self.login_selected
            ),
        ).pack(
            side=LEFT
        )

        ttk.Button(
            actions,
            text="Delete Selected",
            command=(
                self.delete_selected
            ),
        ).pack(
            side=LEFT,
            padx=(8, 0),
        )

        ttk.Button(
            actions,
            text="Refresh",
            command=(
                self.refresh_records
            ),
        ).pack(
            side=LEFT,
            padx=(8, 0),
        )

        ttk.Label(
            actions,
            textvariable=(
                self.status_var
            ),
        ).pack(
            side=RIGHT
        )

        ttk.Label(
            main,
            text=(
                f"Database: {db_path}\n"
                f"Key: {key_path}"
            ),
        ).pack(
            fill=X,
            pady=(8, 0),
        )

    def clear_form(
        self,
    ) -> None:

        self.label_var.set("")
        self.url_var.set("")
        self.username_var.set("")
        self.password_var.set("")

        self.username_selector_var.set(
            DEFAULT_USERNAME_SELECTOR
        )

        self.password_selector_var.set(
            DEFAULT_PASSWORD_SELECTOR
        )

        self.submit_selector_var.set(
            DEFAULT_SUBMIT_SELECTOR
        )

    def add_record(
        self,
    ) -> None:

        try:
            url = validate_url(
                self.url_var.get()
            )

        except ValueError as exc:
            messagebox.showerror(
                "Invalid URL",
                str(exc),
            )
            return

        label = (
            self.label_var
            .get()
            .strip()
        )

        username = (
            self.username_var.get()
        )

        password = (
            self.password_var.get()
        )

        username_selector = (
            self.username_selector_var
            .get()
            .strip()
        )

        password_selector = (
            self.password_selector_var
            .get()
            .strip()
        )

        submit_selector = (
            self.submit_selector_var
            .get()
            .strip()
        )

        if not label:
            label = (
                urlparse(url).hostname
                or "Website"
            )

        if (
            not username
            or not password
        ):
            messagebox.showerror(
                "Missing Credentials",
                (
                    "Username and password "
                    "are required."
                ),
            )
            return

        if (
            not username_selector
            or not password_selector
        ):
            messagebox.showerror(
                "Missing Selector",
                (
                    "Username and password "
                    "CSS selectors are required."
                ),
            )
            return

        try:
            self.database.add_record(
                label=label,
                encrypted_url=(
                    self.cipher.encrypt(
                        url
                    )
                ),
                encrypted_username=(
                    self.cipher.encrypt(
                        username
                    )
                ),
                encrypted_password=(
                    self.cipher.encrypt(
                        password
                    )
                ),
                username_selector=(
                    username_selector
                ),
                password_selector=(
                    password_selector
                ),
                submit_selector=(
                    submit_selector
                ),
            )

        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                (
                    "Could not save "
                    f"record:\n{exc}"
                ),
            )
            return

        self.password_var.set("")

        self.refresh_records()

        self.status_var.set(
            f"Saved: {label}"
        )

    def refresh_records(
        self,
    ) -> None:

        for item in (
            self.tree.get_children()
        ):
            self.tree.delete(
                item
            )

        try:
            records = (
                self.database
                .list_records()
            )

        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                (
                    "Could not load "
                    f"records:\n{exc}"
                ),
            )
            return

        for record in records:
            try:
                url = (
                    self.cipher.decrypt(
                        record.url
                    )
                )

                username = (
                    self.cipher.decrypt(
                        record.username
                    )
                )

            except ValueError:
                url = (
                    "<cannot decrypt>"
                )

                username = (
                    "<cannot decrypt>"
                )

            label = (
                record.label.strip()
            )

            if not label:
                parsed = urlparse(url)

                label = (
                    parsed.hostname
                    or "Imported Record"
                )

            self.tree.insert(
                "",
                END,
                iid=str(
                    record.id
                ),
                values=(
                    label,
                    url,
                    username,
                ),
            )

        self.status_var.set(
            f"{len(records)} record(s)."
        )

    def selected_id(
        self,
    ) -> int | None:

        selection = (
            self.tree.selection()
        )

        if not selection:
            messagebox.showinfo(
                "No Selection",
                (
                    "Select a stored "
                    "record first."
                ),
            )
            return None

        try:
            return int(
                selection[0]
            )

        except ValueError:
            messagebox.showerror(
                "Invalid Selection",
                (
                    "The selected database "
                    "row is invalid."
                ),
            )

            return None

    def delete_selected(
        self,
    ) -> None:

        record_id = (
            self.selected_id()
        )

        if record_id is None:
            return

        values = self.tree.item(
            str(record_id),
            "values",
        )

        label = (
            values[0]
            if values
            else "record"
        )

        if not messagebox.askyesno(
            "Delete Record",
            f"Delete '{label}'?",
        ):
            return

        try:
            deleted = (
                self.database
                .delete_record(
                    record_id
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                (
                    "Could not delete "
                    f"record:\n{exc}"
                ),
            )
            return

        if not deleted:
            messagebox.showwarning(
                "Not Found",
                (
                    "The record "
                    "no longer exists."
                ),
            )

        self.refresh_records()

    def login_selected(
        self,
    ) -> None:

        record_id = (
            self.selected_id()
        )

        if record_id is None:
            return

        record = (
            self.database
            .get_record(
                record_id
            )
        )

        if record is None:
            messagebox.showerror(
                "Not Found",
                (
                    "The selected record "
                    "no longer exists."
                ),
            )

            self.refresh_records()
            return

        try:
            url = validate_url(
                self.cipher.decrypt(
                    record.url
                )
            )

            username = (
                self.cipher.decrypt(
                    record.username
                )
            )

            password = (
                self.cipher.decrypt(
                    record.password
                )
            )

        except ValueError as exc:
            messagebox.showerror(
                "Decryption Error",
                str(exc),
            )
            return

        username_selector = (
            record.username_selector
            .strip()
            or DEFAULT_USERNAME_SELECTOR
        )

        password_selector = (
            record.password_selector
            .strip()
            or DEFAULT_PASSWORD_SELECTOR
        )

        submit_selector = (
            record.submit_selector
            .strip()
        )

        self.status_var.set(
            "Opening browser..."
        )

        self.root.update_idletasks()

        driver = None

        try:
            driver = (
                self.create_driver()
            )

            driver.get(
                url
            )

            wait = WebDriverWait(
                driver,
                20,
            )

            username_field = (
                wait.until(
                    EC.visibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            username_selector,
                        )
                    )
                )
            )

            username_field.clear()

            username_field.send_keys(
                username
            )

            password_field = (
                wait.until(
                    EC.visibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            password_selector,
                        )
                    )
                )
            )

            password_field.clear()

            password_field.send_keys(
                password
            )

            if submit_selector:
                submit = (
                    wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                submit_selector,
                            )
                        )
                    )
                )

                submit.click()

            else:
                password_field.send_keys(
                    Keys.ENTER
                )

        except WebDriverException as exc:
            if driver is not None:
                try:
                    driver.quit()
                except WebDriverException:
                    pass

            messagebox.showerror(
                "Browser Automation Error",
                (
                    "Login automation failed.\n\n"
                    "Check the URL, browser installation, "
                    "and CSS selectors.\n\n"
                    f"{exc}"
                ),
            )

            self.status_var.set(
                "Login failed."
            )

            return

        self.drivers.append(
            driver
        )

        self.status_var.set(
            "Credentials submitted."
        )

    def create_driver(
        self,
    ):
        if self.browser == "chrome":
            options = (
                webdriver.ChromeOptions()
            )

            if self.browser_binary:
                options.binary_location = (
                    self.browser_binary
                )

            return webdriver.Chrome(
                options=options
            )

        if self.browser == "firefox":
            options = (
                webdriver.FirefoxOptions()
            )

            if self.browser_binary:
                options.binary_location = (
                    self.browser_binary
                )

            return webdriver.Firefox(
                options=options
            )

        options = (
            webdriver.EdgeOptions()
        )

        if self.browser_binary:
            options.binary_location = (
                self.browser_binary
            )

        return webdriver.Edge(
            options=options
        )

    def close(
        self,
    ) -> None:

        for driver in self.drivers:
            try:
                driver.quit()

            except WebDriverException:
                pass

        self.root.destroy()


def main() -> int:
    args = parse_args()

    db_path = Path(
        args.db_file
    ).expanduser()

    key_path = Path(
        args.key_file
    ).expanduser()

    try:
        cipher = VaultCipher(
            load_or_create_key(
                key_path
            )
        )

        database = Database(
            db_path
        )

    except (
        OSError,
        ValueError,
    ) as exc:
        print(
            f"[ERROR] {exc}",
            file=sys.stderr,
        )

        return 1

    root = Tk()

    AutoLoginApp(
        root,
        database,
        cipher,
        args.browser,
        args.browser_binary,
        db_path,
        key_path,
    )

    root.mainloop()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
