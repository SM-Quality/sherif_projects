"""
Splunk Chart Exporter - Compact GUI
=====================================
Run:   python splunk_exporter_gui.py
Build: pyinstaller --onefile --windowed --name "SplunkExporter" splunk_exporter_gui.py
"""

import os, sys, time, threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Theme ─────────────────────────────────────────────────────────────────────
BG       = "#0d0d0f"
SURFACE  = "#111115"
SURFACE2 = "#18181c"
RED      = "#c0392b"
RED_DIM  = "#7a1f16"
RED_PALE = "#1a0605"
TEXT     = "#cccccc"
TEXT_DIM = "#666666"
TEXT_MUT = "#444444"
BORDER   = "#2a2a2e"
BORDER2  = "#1e1e22"
MONO     = ("Consolas", 9)
MONO_SM  = ("Consolas", 8)
MONO_LG  = ("Consolas", 10, "bold")


class CollapsibleSection(tk.Frame):
    """A header that toggles a body frame open/closed."""

    def __init__(self, parent, title, icon_char="●", start_open=True, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._open = start_open

        # Border line top
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")

        # Header row
        hdr = tk.Frame(self, bg=SURFACE, cursor="hand2")
        hdr.pack(fill="x")

        # Icon pill
        pill = tk.Frame(hdr, bg=RED_PALE, padx=4, pady=2)
        pill.pack(side="left", padx=(10, 6), pady=6)
        tk.Label(pill, text=icon_char, font=("Consolas", 7),
                 fg=RED, bg=RED_PALE).pack()

        tk.Label(hdr, text=title, font=("Consolas", 9, "bold"),
                 fg=TEXT, bg=SURFACE).pack(side="left")

        self._chev = tk.Label(hdr, text="▾" if start_open else "›",
                              font=("Consolas", 9), fg=TEXT_DIM, bg=SURFACE)
        self._chev.pack(side="right", padx=10)

        # Body
        self.body = tk.Frame(self, bg=BG)
        if start_open:
            self.body.pack(fill="x", padx=12, pady=(4, 8))

        # Bind click on entire header
        for w in (hdr, pill, self._chev):
            w.bind("<Button-1>", self._toggle)
        for child in hdr.winfo_children():
            child.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self._open = not self._open
        if self._open:
            self.body.pack(fill="x", padx=12, pady=(4, 8))
            self._chev.config(text="▾")
        else:
            self.body.pack_forget()
            self._chev.config(text="›")


class SplunkExporterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sherif Tool")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build_ui()
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Title bar
        bar = tk.Frame(self, bg=SURFACE, pady=8)
        bar.pack(fill="x")
        tk.Label(bar, text="Sherif Tool", font=MONO,
                 fg=TEXT_DIM, bg=SURFACE).pack(side="left", padx=10)

        # ── Section 1: Connection ─────────────────────────────────────────────
        s1 = CollapsibleSection(self, "Connection", "◉", start_open=True)
        s1.pack(fill="x")
        self.host_var = self._field(s1.body, "Host",      "https://10.21.127.143")
        self.app_var  = self._field(s1.body, "App",       "Performance_Team")
        self.dash_var = self._field(s1.body, "Dashboard", "sherif_dashboard")

        # ── Section 2: Credentials ────────────────────────────────────────────
        s2 = CollapsibleSection(self, "Credentials", "◈", start_open=True)
        s2.pack(fill="x")
        self.user_var = self._field(s2.body, "Username", "")
        self.pass_var = self._field(s2.body, "Password", "", show="●")

        # ── Section 3: Export Settings ────────────────────────────────────────
        s3 = CollapsibleSection(self, "Export Settings", "◇", start_open=False)
        s3.pack(fill="x")

        # Time range
        tr = tk.Frame(s3.body, bg=BG)
        tr.pack(fill="x", pady=2)
        tk.Label(tr, text="Time Range", font=MONO_SM, fg=TEXT_DIM,
                 bg=BG, width=11, anchor="w").pack(side="left")
        self.time_var = tk.StringVar(value="-24h")
        cb = ttk.Combobox(tr, textvariable=self.time_var,
                          values=["-1h", "-4h", "-24h", "-7d", "-30d"],
                          font=MONO_SM, width=8, state="readonly")
        cb.pack(side="left")

        # Output folder
        self.out_var = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        self._browse_field(s3.body, "Save To",     self.out_var, self._pick_folder)

        # ChromeDriver — look next to the .exe first, then fall back to full path
        _base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
        _local = os.path.join(_base, "chromedriver.exe")
        _default = _local if os.path.exists(_local) else r"C:\Users\V21SAbdallah1\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
        self.drv_var = tk.StringVar(value=_default)
        self._browse_field(s3.body, "ChromeDriver", self.drv_var, self._pick_driver)

        # ── Export button ─────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")
        btn_frame = tk.Frame(self, bg=SURFACE, pady=10)
        btn_frame.pack(fill="x")
        self.run_btn = tk.Button(
            btn_frame, text="▶  Import Chart",
            font=MONO_LG, fg="#ffffff", bg=RED,
            bd=0, relief="flat", cursor="hand2",
            activebackground=RED_DIM, activeforeground="#fff",
            command=self._run, padx=20, pady=7
        )
        self.run_btn.pack(fill="x", padx=12)

        # ── Log ───────────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")
        log_hdr = tk.Frame(self, bg=BG, pady=4)
        log_hdr.pack(fill="x", padx=12)
        tk.Label(log_hdr, text="LOG", font=("Consolas", 7, "bold"),
                 fg=TEXT_MUT, bg=BG).pack(side="left")
        tk.Button(log_hdr, text="clear", font=("Consolas", 7),
                  fg=TEXT_MUT, bg=BG, bd=0, relief="flat",
                  cursor="hand2", activebackground=BG,
                  command=self._clear_log).pack(side="right")

        self.log = tk.Text(self, font=("Consolas", 8), bg=BG, fg=TEXT_DIM,
                           relief="flat", bd=0, state="disabled",
                           wrap="word", height=7, width=48,
                           insertbackground=RED)
        self.log.pack(fill="x", padx=12, pady=(0, 4))

        # Status bar
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")
        sb = tk.Frame(self, bg=SURFACE, pady=5)
        sb.pack(fill="x")
        tk.Label(sb, text="●", font=("Consolas", 7),
                 fg=RED, bg=SURFACE).pack(side="left", padx=(10, 4))
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self.status_var, font=MONO_SM,
                 fg=TEXT_DIM, bg=SURFACE).pack(side="left")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _field(self, parent, label, default, show=None):
        var = tk.StringVar(value=default)
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=2)
        tk.Label(f, text=label, font=MONO_SM, fg=TEXT_DIM,
                 bg=BG, width=11, anchor="w").pack(side="left")
        e = tk.Entry(f, textvariable=var, font=MONO_SM,
                     bg=SURFACE2, fg=TEXT, insertbackground=RED,
                     relief="flat", bd=0, show=show or "",
                     highlightbackground=BORDER, highlightthickness=1)
        e.pack(side="left", fill="x", expand=True, ipady=5)
        return var

    def _browse_field(self, parent, label, var, cmd):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=2)
        tk.Label(f, text=label, font=MONO_SM, fg=TEXT_DIM,
                 bg=BG, width=11, anchor="w").pack(side="left")
        tk.Entry(f, textvariable=var, font=("Consolas", 7),
                 bg=SURFACE2, fg=TEXT_DIM, insertbackground=RED,
                 relief="flat", bd=0,
                 highlightbackground=BORDER, highlightthickness=1
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 4))
        tk.Button(f, text="Browse", font=MONO_SM, fg=RED,
                  bg=RED_PALE, bd=0, relief="flat", cursor="hand2",
                  activebackground=SURFACE2, activeforeground=RED,
                  command=cmd).pack(side="left", ipadx=6, ipady=3)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d: self.out_var.set(d)

    def _pick_driver(self):
        p = filedialog.askopenfilename(
            title="Select chromedriver.exe",
            filetypes=[("Executable", "*.exe"), ("All", "*.*")])
        if p: self.drv_var.set(p)

    # ── Logging ───────────────────────────────────────────────────────────────
    def _log(self, msg, tag="n"):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.tag_config("ok",  foreground=RED)
        self.log.tag_config("err", foreground="#ff6b6b")
        self.log.tag_config("w",   foreground="#f5a623")
        self.log.tag_config("d",   foreground=TEXT_MUT)
        self.log.tag_config("n",   foreground=TEXT_DIM)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ── Run ───────────────────────────────────────────────────────────────────
    def _run(self):
        if not self.user_var.get().strip():
            messagebox.showerror("Missing", "Enter your Username."); return
        if not self.pass_var.get().strip():
            messagebox.showerror("Missing", "Enter your Password."); return
        if not self.drv_var.get().strip():
            messagebox.showerror("Missing",
                "Select your chromedriver.exe via Browse."); return

        self.run_btn.configure(state="disabled", text="⏳  Running…",
                               bg=SURFACE2, fg=TEXT_DIM)
        self.status_var.set("Running export…")
        threading.Thread(target=self._thread, daemon=True).start()

    def _thread(self):
        try:
            self._export(
                splunk_host = self.host_var.get().strip(),
                app         = self.app_var.get().strip(),
                dashboard   = self.dash_var.get().strip(),
                username    = self.user_var.get().strip(),
                password    = self.pass_var.get().strip(),
                time_range  = self.time_var.get().strip(),
                output_dir  = self.out_var.get().strip(),
                driver_path = self.drv_var.get().strip(),
            )
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ {e}", "err"))
        finally:
            self.after(0, self._reset)

    def _reset(self):
        self.run_btn.configure(state="normal", text="▶  Import Chart",
                               bg=RED, fg="#ffffff")
        self.status_var.set("Done.")

    # ── Core export logic ─────────────────────────────────────────────────────
    def _export(self, splunk_host, app, dashboard, username, password,
                time_range, output_dir, driver_path):

        def log(msg, tag="n"):
            self.after(0, lambda m=msg, t=tag: self._log(m, t))

        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.action_chains import ActionChains

        opts = Options()
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--ignore-ssl-errors")
        opts.add_argument("--window-size=1920,1080")
        opts.add_experimental_option("prefs", {
            "download.default_directory":   output_dir.replace("/", "\\"),
            "download.prompt_for_download": False,
            "download.directory_upgrade":   True,
            "safebrowsing.enabled":         True,
        })

        # Fast login via requests API
        import requests, urllib3
        urllib3.disable_warnings()
        log("Authenticating via API…", "d")
        http = requests.Session()
        http.verify = False
        http.get(f"{splunk_host}/en-US/account/login")
        cval = http.cookies.get("cval", "")
        login_resp = http.post(
            f"{splunk_host}/en-US/account/login",
            data={"username": username, "password": password,
                  "cval": cval, "return_to": "/en-US/"}
        )
        if login_resp.status_code != 200 or "splunkd_443" not in http.cookies:
            log("❌ API login failed — check credentials.", "err")
            return
        log("✔ Authenticated via API!", "ok")

        log("Starting Chrome…", "d")
        driver = webdriver.Chrome(service=Service(driver_path), options=opts)
        wait   = WebDriverWait(driver, 30)
        act    = ActionChains(driver)

        try:
            # Inject session cookies into Chrome (skip login page)
            driver.get(f"{splunk_host}/en-US/account/login")
            # Wait only until page is ready, not a fixed delay
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            for name, value in http.cookies.items():
                try:
                    driver.add_cookie({
                        "name": name, "value": value,
                        "domain": splunk_host.replace("https://", ""),
                        "path": "/"
                    })
                except Exception:
                    pass
            log("✔ Session injected into browser!", "ok")

            # 2. Load dashboard
            log("Loading dashboard…")
            driver.get(
                f"{splunk_host}/en-US/app/{app}/{dashboard}"
                f"?form.global_time.earliest={time_range}&form.global_time.latest=now"
            )
            # Wait for chart container to appear
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".highcharts-container")))
            # Then wait until chart actually has data series rendered
            wait.until(lambda d: len(d.find_elements(
                By.CSS_SELECTOR, ".highcharts-series-group .highcharts-series")) > 0)
            log("✔ Chart loaded!", "ok")

            # 3. Hover to reveal toolbar (no sleep needed — just move)
            log("Revealing toolbar…", "d")
            chart = driver.find_element(By.CSS_SELECTOR, ".highcharts-container")
            act.move_to_element(chart).perform()

            # Wait for toolbar buttons to appear
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button.sc-bKNmIE.jrVnv")))

            # 4. Find Export button by SVG title
            log("Finding Export button…", "d")
            buttons = driver.find_elements(
                By.CSS_SELECTOR, "button.sc-bKNmIE.jrVnv")
            export_btn = None
            for btn in buttons:
                title = driver.execute_script(
                    "return arguments[0].querySelector('title')"
                    " ? arguments[0].querySelector('title').textContent : '';",
                    btn)
                if title.strip().lower() == "export":
                    export_btn = btn
                    break

            if not export_btn:
                log("❌ Export button not found.", "err"); return

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", export_btn)
            driver.execute_script("arguments[0].click();", export_btn)
            log("✔ Clicked Export button!", "ok")

            # 5. Wait for dialog then fill filename
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Export visualization')]")))
            try:
                for inp in driver.find_elements(
                        By.CSS_SELECTOR, "input[type='text']"):
                    if inp.is_displayed() and inp.is_enabled():
                        inp.clear()
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        inp.send_keys(f"sherif_chart_{ts}")
                        log(f"Filename: sherif_chart_{ts}", "d")
                        break
            except Exception as e:
                log(f"Filename: {e}", "w")

            # 6. Click Export in dialog
            clicked = False
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if btn.is_displayed() and btn.text.strip().lower() == "export":
                    driver.execute_script("arguments[0].click();", btn)
                    log("✔ Clicked Export in dialog!", "ok")
                    clicked = True
                    break
            if not clicked:
                log("❌ Export dialog button not found.", "err"); return

            # 7. Wait for file to appear in output dir (poll instead of fixed sleep)
            log("Waiting for download…", "d")
            before = set(os.listdir(output_dir))
            for _ in range(30):  # max 15 seconds
                time.sleep(0.5)
                after = set(os.listdir(output_dir))
                new_files = [f for f in after - before if f.endswith('.png')]
                if new_files:
                    full = os.path.join(output_dir, new_files[0])
                    log(f"✅ Saved: {new_files[0]}", "ok")
                    self.after(0, lambda p=full: messagebox.showinfo(
                        "Done!", f"Chart saved to:\n{p}"))
                    break
            else:
                log("✅ Check your output folder!", "ok")

        finally:
            driver.quit()
            log("Browser closed.", "d")


if __name__ == "__main__":
    SplunkExporterApp().mainloop()