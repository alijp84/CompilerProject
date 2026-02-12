# -*- coding: utf-8 -*-
"""
Persian/English DSL Compiler - Final Bilingual Version
✓ Perfect bidirectional text: RTL (right-to-left) for Persian, LTR (left-to-right) for English
✓ Clean empty workspace - NO placeholder clutter
✓ Fixed initialization order (no AttributeError)
✓ Fixed English suggestion engine with ASCII detection
✓ English-only help guide in English mode
✓ Section headers properly commented with #
✓ Fixed ScrolledText justify using tags (rtl/ltr)
"""
import os
import sys
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, font as tkfont, Toplevel, Listbox
import threading
import re

try:
    from compiler_core import run_compiler
except ImportError:
    messagebox.showerror("Error", "compiler_core.py not found!\nPlease place both files in the same directory.")
    sys.exit(1)

# ==================== TYPO DETECTION (PERSIAN ONLY) ====================
class TypoSuggester:
    """Detects genuine Persian typos without false positives"""
    def __init__(self):
        self.typo_rules = [
            (r'\bذف_ستون\b', 'حذف_ستون', 'Typo: "ذف_ستون" → should be "حذف_ستون"'),
            (r'\bتغیر_نام\b', 'تغییر_نام', 'Typo: "تغیر_نام" → should be "تغییر_نام"'),
        ]

    def check_typos(self, code):
        suggestions = []
        clean_code = code.replace('\u200f', '').replace('\u200e', '')
        lines = [line.strip() for line in clean_code.split('\n') if line.strip()]

        for line_num, line in enumerate(lines, 1):
            for typo_pattern, correct_cmd, msg in self.typo_rules:
                if (re.search(typo_pattern, line) and
                    not re.search(r'\b' + re.escape(correct_cmd) + r'\b', line)):
                    match = re.search(typo_pattern, line)
                    if match:
                        suggestions.append({
                            'line': line_num,
                            'typo': match.group(),
                            'correct': correct_cmd,
                            'message': msg
                        })
        return suggestions

# ==================== BILINGUAL SUGGESTION ENGINE (FIXED ENGLISH SUPPORT) ====================
class BilingualSuggestionEngine:
    def __init__(self):
        # Persian templates
        self.fa_templates = {
            "بگیر از": [
                ('بگیر از "lab_data.csv" به نام df', 'quote'),
                ('بگیر از "داده‌ها.csv" به نام دیتافریم', 'quote')
            ],
            "پاکسازی": [
                ('پاکسازی df : حذف تکراری', 'colon'),
                ('پاکسازی df : حذف کلی خالی', 'colon'),
                ('پاکسازی df : حذف age خالی', 'colon'),
                ('پاکسازی df : جایگزینی کلی خالی با میانگین', 'colon'),
                ('پاکسازی df : جایگزینی glucose خالی با میانگین', 'colon')
            ],
            "فیلتر": [
                ('فیلتر df : وقتی age > 15', 'colon'),
                ('فیلتر df : وقتی gender == "Female"', 'quote'),
                ('فیلتر df : glucose بین 90 و 120', 'colon'),
                ('فیلتر_ترکیبی df : age > 20 و cholesterol < 220', 'colon')
            ],
            "ایجاد_ستون": [
                ('ایجاد_ستون df : risk_score = ((0.1 * glucose) + (0.9 * cholesterol))', 'colon'),
                ('ایجاد_ستون df : سن_گروه = age // 10', 'colon')
            ],
            "ذخیره": [
                ('ذخیره df : در "processed_data.csv"', 'quote'),
                ('ذخیره دیتافریم : در "گزارش.xlsx"', 'quote')
            ],
            "نمودار": [
                ('نمودار df : هیستوگرام age', 'colon'),
                ('نمودار df : میانگین cholesterol در gender', 'colon'),
                ('نمودار df : پراکندگی glucose در cholesterol', 'colon'),
                ('نمودار df : جعبه‌ای age در gender', 'colon'),
                ('نمودار df : نقشه_حرارتی', 'end')
            ],
            "مرتب_سازی": [
                ('مرتب_سازی df : age صعودی', 'colon'),
                ('مرتب_سازی دیتافریم : حقوق نزولی', 'colon')
            ],
            "تغییر_نام": [
                ('تغییر_نام df : glucose به قند_خون', 'colon'),
                ('تغییر_نام دیتافریم : قد به ارتفاع', 'colon')
            ],
            "نرمال_سازی": [
                ('نرمال_سازی df : ستون age', 'colon'),
                ('نرمال_سازی دیتافریم : ستون درآمد', 'colon')
            ],
            "حذف_ستون": [
                ('حذف_ستون df : id', 'colon'),
                ('حذف_ستون df : cholesterol', 'colon')
            ],
            "سطح_بندی": [
                ('سطح_بندی df : در age به 0:جوان 30:میانسال 50:مسن', 'colon'),
                ('سطح_بندی دیتافریم : در نمره به 0:ضعیف 5:متوسط 10:خوب', 'colon')
            ]
        }
        
        # English templates
        self.en_templates = {
            "LOAD": [
                ('LOAD "lab_data.csv" INTO df', 'end'),
                ('LOAD "data.csv" INTO data', 'end')
            ],
            "CLEAN": [
                ('CLEAN df DROP_DUPLICATES', 'end'),
                ('CLEAN df DROP_ALL null', 'end'),
                ('CLEAN df DROP_SPECIFIC age null', 'end'),
                ('CLEAN df FILL_ALL null mean', 'end'),
                ('CLEAN df FILL_SPECIFIC glucose null mean', 'end')
            ],
            "FILTER": [
                ('FILTER df WHERE age > 15', 'end'),
                ('FILTER df WHERE gender == "Female"', 'quote'),
                ('FILTER_RANGE df glucose 90 120', 'end'),
                ('FILTER_COMPLEX df age > 20 and cholesterol < 220', 'end')
            ],
            "CREATE_COL": [
                ('CREATE_COL df : risk_score = ((0.1 * glucose) + (0.9 * cholesterol))', 'colon'),
                ('CREATE_COL df : age_group = age // 10', 'colon')
            ],
            "SAVE": [
                ('SAVE df TO "processed_data.csv"', 'quote'),
                ('SAVE results TO "report.xlsx"', 'quote')
            ],
            "PLOT": [
                ('PLOT df HIST OF age IN ALL', 'end'),
                ('PLOT df MEAN OF cholesterol IN gender', 'end'),
                ('PLOT df SCAT OF glucose IN cholesterol', 'end'),
                ('PLOT df BOX OF age IN gender', 'end'),
                ('PLOT df HEATMAP OF ALL IN ALL', 'end')
            ],
            "SORT": [
                ('SORT df BY age ASC', 'end'),
                ('SORT df BY salary DESC', 'end')
            ],
            "RENAME": [
                ('RENAME df COL glucose TO blood_sugar', 'end'),
                ('RENAME df COL height TO stature', 'end')
            ],
            "NORMALIZE": [
                ('NORMALIZE df COL age', 'end'),
                ('NORMALIZE df COL income', 'end')
            ],
            "DROP_COL": [
                ('DROP_COL df id', 'end'),
                ('DROP_COL df cholesterol', 'end')
            ],
            "LEVELING": [
                ('LEVELING df age 0:young 30:middle 50:senior', 'end'),
                ('LEVELING df score 0:low 5:medium 10:high', 'end')
            ]
        }
        
        # Build prefix indexes
        self.fa_prefix_index = self._build_prefix_index(self.fa_templates)
        self.en_prefix_index = self._build_prefix_index(self.en_templates)
    
    def _build_prefix_index(self, templates):
        index = {}
        for keyword, _ in templates.items():
            for i in range(1, min(4, len(keyword) + 1)):
                prefix = keyword[:i]
                if prefix not in index:
                    index[prefix] = []
                index[prefix].append(keyword)
        return index
    
    def get_suggestions(self, current_text, cursor_pos, language="fa"):
        if not current_text or cursor_pos <= 0:
            return []
        
        clean_text = current_text.replace('\u200f', '').replace('\u200e', '')
        text_before = clean_text[:cursor_pos]
        last_space = max(text_before.rfind(' '), text_before.rfind('\n'))
        current_word = text_before[last_space + 1:] if last_space != -1 else text_before.strip()
        
        # Handle context after colon
        if ':' in current_word and not current_word.strip().endswith(':'):
            parts = current_word.split(':')
            if len(parts) > 1:
                context = parts[0].strip()
                templates = self.fa_templates if language == "fa" else self.en_templates
                if context in templates:
                    return [(context, templates[context])]
                return []
        
        # Return starter suggestions for empty/short input
        if not current_word or len(current_word) < 2:
            if language == "fa":
                return [
                    ("بگیر از", self.fa_templates["بگیر از"]),
                    ("پاکسازی", self.fa_templates["پاکسازی"]),
                    ("فیلتر", self.fa_templates["فیلتر"]),
                    ("ایجاد_ستون", self.fa_templates["ایجاد_ستون"]),
                    ("ذخیره", self.fa_templates["ذخیره"])
                ]
            else:
                return [
                    ("LOAD", self.en_templates["LOAD"]),
                    ("CLEAN", self.en_templates["CLEAN"]),
                    ("FILTER", self.en_templates["FILTER"]),
                    ("CREATE_COL", self.en_templates["CREATE_COL"]),
                    ("SAVE", self.en_templates["SAVE"])
                ]
        
        lookup_key = current_word
        is_english = all(ord(c) < 128 for c in lookup_key if c.strip())
        
        if language == "en" or is_english:
            templates = self.en_templates
            prefix_index = self.en_prefix_index
        else:
            templates = self.fa_templates
            prefix_index = self.fa_prefix_index
        
        # Exact match
        if lookup_key in templates:
            return [(lookup_key, templates[lookup_key])]
        
        # Prefix match - case-insensitive for English
        suggestions = []
        for prefix, keywords in prefix_index.items():
            if language == "en" or is_english:
                if lookup_key.lower().startswith(prefix.lower()):
                    for kw in keywords:
                        if kw not in [s[0] for s in suggestions]:
                            suggestions.append((kw, templates[kw]))
            else:
                if lookup_key.startswith(prefix):
                    for kw in keywords:
                        if kw not in [s[0] for s in suggestions]:
                            suggestions.append((kw, templates[kw]))
        
        return suggestions[:8]

# ==================== NON-BLOCKING POPUP (BILINGUAL) ====================
class SuggestionPopup:
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.popup = None
        self.listbox = None
        self.visible = False
        self.selected_index = 0
        
        persian_fonts = ["B Nazanin", "B Titr", "Vazir", "Iran Sans", "Arial", "Tahoma"]
        available = tkfont.families()
        self.font = next((f for f in persian_fonts if f in available), "Arial")

    def show(self, suggestions, x, y, language="fa"):
        self.hide()
        if not suggestions:
            return

        self.popup = Toplevel(self.parent)
        self.popup.wm_overrideredirect(True)
        self.popup.wm_geometry(f"+{x}+{y}")
        self.popup.configure(bg="#f0f0f0")
        self.popup.attributes('-topmost', True)
        self.popup.bind("<FocusIn>", lambda e: self.text_widget.focus_set())

        frame = tk.Frame(self.popup, borderwidth=1, relief="solid", bg="white")
        frame.pack(padx=1, pady=1)

        self.listbox = Listbox(
            frame,
            font=(self.font, 11),
            bg="white",
            fg="#2c3e50",
            selectbackground="#3498db",
            selectforeground="white",
            activestyle="none",
            height=min(len(suggestions), 8),
            width=70,
            borderwidth=0,
            highlightthickness=0
        )
        self.listbox.pack(padx=2, pady=2)

        for i, (keyword, templates) in enumerate(suggestions):
            display = f"{keyword} • {templates[0][0]}" if templates else keyword
            if language == "fa" and self._is_persian(keyword):
                self.listbox.insert(tk.END, "   " + display)
            else:
                self.listbox.insert(tk.END, display)

        self.listbox.bind("<ButtonRelease-1>", self._on_click_select)
        self.listbox.bind("<Return>", self._on_key_select)
        self.listbox.bind("<Tab>", self._on_key_select)
        self.listbox.bind("<Escape>", lambda e: self.hide())

        self.selected_index = 0
        self._update_selection()
        self.visible = True

    def _is_persian(self, text):
        return any('\u0600' <= c <= '\u06FF' for c in text)

    def _update_selection(self):
        if not self.listbox or not self.listbox.winfo_exists():
            return
        self.listbox.selection_clear(0, tk.END)
        if 0 <= self.selected_index < self.listbox.size():
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)

    def _on_click_select(self, event):
        if not self.listbox.curselection():
            return "break"
        index = self.listbox.curselection()[0]
        self._apply_suggestion(index)
        self.hide()
        self.text_widget.focus_set()
        return "break"

    def _on_key_select(self, event):
        self._apply_suggestion(self.selected_index)
        self.hide()
        self.text_widget.focus_set()
        return "break"

    def _apply_suggestion(self, index):
        if hasattr(self.parent, 'on_suggestion_selected'):
            self.parent.on_suggestion_selected(index)

    def navigate(self, direction):
        if not self.visible or not self.listbox or not self.listbox.winfo_exists():
            return False
        prev_index = self.selected_index
        if direction == "up":
            self.selected_index = max(0, self.selected_index - 1)
        elif direction == "down":
            self.selected_index = min(self.listbox.size() - 1, self.selected_index + 1)
        if self.selected_index != prev_index:
            self._update_selection()
            return True
        return False

    def get_selected_index(self):
        return self.selected_index

    def hide(self):
        if self.popup and self.popup.winfo_exists():
            try:
                self.popup.destroy()
            except:
                pass
        self.popup = None
        self.visible = False
        self.selected_index = 0

# ==================== MAIN BILINGUAL GUI ====================
class PersianCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Persian/English DSL Compiler v3.1")
        self.root.geometry("1150x800")
        self.root.minsize(950, 650)
        self.root.configure(bg="#f8f9fa")
        
        # Language state
        self.current_language = "fa"  # "fa" or "en"
        self.RLM = '\u200f'  # Right-to-Left Mark (invisible character for RTL)
        self.LRM = '\u200e'  # Left-to-Right Mark (invisible character for LTR)
        
        self.suggestion_engine = BilingualSuggestionEngine()
        self.typo_suggester = TypoSuggester()
        self.suggestion_popup = SuggestionPopup(root, None)
        self.suggestion_timer = None

        persian_fonts = ["B Nazanin", "B Titr", "Vazir", "Iran Sans", "Arial", "Tahoma", "Segoe UI"]
        available_fonts = tkfont.families()
        self.base_font = next((f for f in persian_fonts if f in available_fonts), "Arial")
        self.en_font = "Consolas" if "Consolas" in available_fonts else "Courier New"

        self.setup_styles()
        self.create_widgets()
        self.suggestion_popup.text_widget = self.input_text

        # Bindings
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Up>", self._on_arrow_key)
        self.input_text.bind("<Down>", self._on_arrow_key)
        self.input_text.bind("<KeyRelease>", self._on_key_release)
        self.input_text.bind("<KeyPress>", self._on_key_press)
        self.input_text.bind("<ButtonRelease-1>", self._on_mouse_click)
        self.root.bind('<Control-Return>', lambda e: self.compile_code())
        self.root.bind('<Control-o>', lambda e: self.load_file())
        self.root.bind('<Control-l>', lambda e: self.toggle_language())  # Ctrl+L to toggle language

    def setup_styles(self):
        self.colors = {
            'primary': '#255c82',
            'secondary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'bg_input': '#ffffff',
            'bg_output': '#f8f9fa',
            'border': '#dce4ec'
        }

    def create_widgets(self):
        header = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=self.colors['primary'])
        title_frame.pack(side=tk.LEFT, expand=True)

        self.title_label = tk.Label(
            title_frame,
            text="کامپایلر زبان تخصصی فارسی/انگلیسی",
            font=(self.base_font, 20, "bold"),
            fg="white",
            bg=self.colors['primary']
        )
        self.title_label.pack(pady=(12, 0))

        self.subtitle_label = tk.Label(
            title_frame,
            text="برای پردازش داده‌های آزمایشگاهی (فایل lab_data.csv)",
            font=(self.base_font, 12),
            fg="#a3c1d6",
            bg=self.colors['primary']
        )
        self.subtitle_label.pack(pady=(0, 3))

        # Language toggle button (top-right)
        lang_frame = tk.Frame(header, bg=self.colors['primary'])
        lang_frame.pack(side=tk.RIGHT, padx=20)

        self.lang_button = tk.Button(
            lang_frame,
            text="ENGLISH",
            command=self.toggle_language,
            bg="#1a4766",
            fg="white",
            font=(self.base_font, 11, "bold"),
            padx=15,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.lang_button.pack()

        tip_label = tk.Label(
            header,
            text="💡 Tip: Press ↑/↓ to navigate suggestions | Enter to accept | Ctrl+L to toggle language",
            font=(self.base_font, 10, "bold"),
            fg="#ffd700",
            bg=self.colors['primary']
        )
        tip_label.pack(side=tk.BOTTOM, pady=(0, 8))

        main_container = tk.Frame(self.root, bg="#f8f9fa")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Input frame
        input_frame = tk.LabelFrame(
            main_container,
            text="کد ورودی (فارسی/انگلیسی) - تایپ کنید و با کلید Enter دستور کامل را دریافت کنید",
            font=(self.base_font, 13, "bold"),
            bg="#ffffff",
            relief=tk.GROOVE,
            borderwidth=2
        )
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        btn_container = tk.Frame(input_frame, bg="#ffffff")
        btn_container.pack(fill=tk.X, padx=15, pady=12)

        # Buttons
        self.compile_btn = tk.Button(
            btn_container,
            text="اجرای کامپایل (Ctrl+Enter)",
            command=self.compile_code,
            bg=self.colors['success'],
            fg="white",
            font=(self.base_font, 11, "bold"),
            padx=25,
            pady=9,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.compile_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=8)

        self.load_btn = tk.Button(
            btn_container,
            text="بارگذاری از فایل (Ctrl+O)",
            command=self.load_file,
            bg=self.colors['secondary'],
            fg="white",
            font=(self.base_font, 11, "bold"),
            padx=20,
            pady=9,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.load_btn.pack(side=tk.RIGHT, padx=(10, 5))

        self.clear_btn = tk.Button(
            btn_container,
            text="پاک‌سازی",
            command=self.clear_all,
            bg=self.colors['warning'],
            fg="white",
            font=(self.base_font, 11, "bold"),
            padx=20,
            pady=9,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=(10, 5))

        self.help_btn = tk.Button(
            btn_container,
            text="راهنمای کامل",
            command=self.show_help,
            bg=self.colors['dark'],
            fg="white",
            font=(self.base_font, 11, "bold"),
            padx=20,
            pady=9,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.help_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=(self.base_font, 12),
            bg=self.colors['bg_input'],
            fg="#2c3e50",
            padx=18,
            pady=15,
            relief=tk.FLAT,
            borderwidth=1,
            undo=True,
            maxundo=-1,
            autoseparators=True
        )
        
        # Configure tags for RTL/LTR alignment (CRITICAL FIX FOR ScrolledText)
        self.input_text.tag_configure("rtl", lmargin1=10, lmargin2=10, rmargin=10, justify='right')
        self.input_text.tag_configure("ltr", lmargin1=10, lmargin2=10, rmargin=10, justify='left')
        
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.input_text.focus_set()

        # Output frame
        output_frame = tk.LabelFrame(
            main_container,
            text="خروجی کامپایلر و گزارش اجرایی / Compiler Output & Execution Report",
            font=(self.base_font, 13, "bold"),
            bg="#ffffff",
            relief=tk.GROOVE,
            borderwidth=2
        )
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=(self.base_font, 11),
            bg=self.colors['bg_output'],
            fg="#2c3e50",
            padx=18,
            pady=15,
            relief=tk.FLAT,
            borderwidth=1,
            state=tk.DISABLED,
            spacing1=3,
            spacing2=2,
            spacing3=5
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Text tags for styling
        self.output_text.tag_config("success", foreground=self.colors['success'], font=(self.base_font, 11, "bold"))
        self.output_text.tag_config("error", foreground=self.colors['danger'], font=(self.base_font, 11, "bold"))
        self.output_text.tag_config("warning", foreground=self.colors['warning'], font=(self.base_font, 11, "bold"))
        self.output_text.tag_config("suggestion", foreground=self.colors['secondary'], font=(self.base_font, 11, "italic"))
        self.output_text.tag_config("path", foreground=self.colors['secondary'], font=(self.base_font, 11))
        self.output_text.tag_config("header", foreground=self.colors['dark'], font=(self.base_font, 12, "bold"))
        self.output_text.tag_config("critical", foreground=self.colors['danger'], font=(self.base_font, 11, "bold", "underline"))

        # Status bar with language indicator (MUST BE CREATED BEFORE initialize_clean_input)
        status_frame = tk.Frame(self.root, bg="#e9ecef", height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame,
            text="آماده برای کدنویسی | تایپ کنید تا پیشنهادات ظاهر شوند",
            font=(self.base_font, 10),
            bg="#e9ecef",
            fg="#495057"
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

        self.lang_status = tk.Label(
            status_frame,
            text="🇮🇷 فارسی",
            font=(self.base_font, 10, "bold"),
            bg="#e9ecef",
            fg="#255c82"
        )
        self.lang_status.pack(side=tk.LEFT, padx=20)

        shortcut_label = tk.Label(
            status_frame,
            text="⌨️ Shortcuts: ↑/↓ navigate | Enter accept | Ctrl+L toggle language",
            font=(self.base_font, 10),
            bg="#e9ecef",
            fg="#2c3e50"
        )
        shortcut_label.pack(side=tk.LEFT, padx=(60, 20))

        # Initialize clean input AFTER status_label is created
        self.initialize_clean_input()

    def initialize_clean_input(self):
        """Initialize input area as completely clean and empty with proper text direction"""
        self.input_text.delete("1.0", tk.END)
        
        # Insert directional mark based on current language
        prefix = self.RLM if self.current_language == "fa" else self.LRM
        self.input_text.insert("1.0", prefix)
        
        # Apply correct alignment tag and font
        if self.current_language == "fa":
            self.input_text.tag_add("rtl", "1.0", "end")
            self.input_text.configure(font=(self.base_font, 12))
            # Set status AFTER status_label exists
            self.status_label.config(text="آماده برای کدنویسی | تایپ کنید تا پیشنهادات ظاهر شوند", fg="#495057")
        else:
            self.input_text.tag_add("ltr", "1.0", "end")
            self.input_text.configure(font=(self.en_font, 12))
            self.status_label.config(text="Ready for coding | Type to see suggestions", fg="#495057")

    def toggle_language(self):
        """Toggle between Persian (RTL) and English (LTR) modes"""
        self.current_language = "en" if self.current_language == "fa" else "fa"
        
        # Update UI elements
        if self.current_language == "fa":
            self.lang_button.config(text="ENGLISH")
            self.lang_status.config(text="🇮🇷 فارسی", fg="#255c82")
            self.title_label.config(text="کامپایلر زبان تخصصی فارسی/انگلیسی")
            self.subtitle_label.config(text="برای پردازش داده‌های آزمایشگاهی (فایل lab_data.csv)")
            input_frame_label = "کد ورودی (فارسی/انگلیسی) - تایپ کنید و با کلید Enter دستور کامل را دریافت کنید"
            self.compile_btn.config(text="اجرای کامپایل (Ctrl+Enter)")
            self.load_btn.config(text="بارگذاری از فایل (Ctrl+O)")
            self.clear_btn.config(text="پاک‌سازی")
            self.help_btn.config(text="راهنمای کامل")
        else:
            self.lang_button.config(text="فارسی")
            self.lang_status.config(text="🇬🇧 English", fg="#255c82")
            self.title_label.config(text="Persian/English DSL Compiler")
            self.subtitle_label.config(text="For processing lab data (lab_data.csv file)")
            input_frame_label = "Input Code (Persian/English) - Type and press Enter for full command"
            self.compile_btn.config(text="Compile & Run (Ctrl+Enter)")
            self.load_btn.config(text="Load from File (Ctrl+O)")
            self.clear_btn.config(text="Clear")
            self.help_btn.config(text="Full Help")
        
        # Update input frame label
        self.input_text.master.config(text=input_frame_label)
        
        # Reinitialize clean input with correct direction (RTL/LTR)
        self.initialize_clean_input()
        
        # Notify user
        msg = "Switched to English mode (LTR)" if self.current_language == "en" else "حالت فارسی فعال شد (RTL)"
        self.status_label.config(text=msg, fg=self.colors['secondary'])
        self.root.after(2000, self._restore_status)

    def _restore_status(self):
        """Restore normal status message"""
        if self.current_language == "fa":
            self.status_label.config(
                text="آماده برای کدنویسی | تایپ کنید تا پیشنهادات ظاهر شوند",
                fg="#495057"
            )
        else:
            self.status_label.config(
                text="Ready for coding | Type to see suggestions",
                fg="#495057"
            )

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select DSL Code File" if self.current_language == "en" else "انتخاب فایل کد DSL",
            filetypes=[
                ("Text files", "*.txt"),
                ("DSL files", "*.dsl"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser(".")
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.input_text.delete("1.0", tk.END)
                # Auto-detect language from content
                if any('\u0600' <= c <= '\u06FF' for c in content[:100]):
                    self.current_language = "fa"
                    self.input_text.insert("1.0", self.RLM + content)
                    self.input_text.tag_add("rtl", "1.0", "end")
                    self.input_text.configure(font=(self.base_font, 12))
                else:
                    self.current_language = "en"
                    self.input_text.insert("1.0", self.LRM + content)
                    self.input_text.tag_add("ltr", "1.0", "end")
                    self.input_text.configure(font=(self.en_font, 12))
                
                # Update language button state
                self.lang_button.config(text="فارسی" if self.current_language == "en" else "ENGLISH")
                self.lang_status.config(text="🇬🇧 English" if self.current_language == "en" else "🇮🇷 فارسی")
                
                status_msg = f"✓ File loaded: {os.path.basename(file_path)}" if self.current_language == "en" else f"✓ فایل بارگذاری شد: {os.path.basename(file_path)}"
                self.status_label.config(text=status_msg, fg=self.colors['success'])
            except Exception as e:
                error_msg = f"Error reading file:\n{str(e)}" if self.current_language == "en" else f"خطا در خواندن فایل:\n{str(e)}"
                messagebox.showerror("File Load Error" if self.current_language == "en" else "خطا در بارگذاری", error_msg)
                self.status_label.config(text="✗ File load error" if self.current_language == "en" else "✗ خطا در بارگذاری فایل", fg=self.colors['danger'])

    def clear_all(self):
        self.initialize_clean_input()
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        status_msg = "Cleared | Ready for new code" if self.current_language == "en" else "پاک‌سازی انجام شد | آماده برای کد جدید"
        self.status_label.config(text=status_msg, fg=self.colors['warning'])
        self.suggestion_popup.hide()

    def show_help(self):
        # English-only help in English mode (no Persian characters)
        if self.current_language == "en":
            help_text = (
                "Complete Guide for Persian/English DSL Compiler\n"
                "========================================\n\n"
                "📌 Key Features:\n"
                "   • Supports both Persian (RTL) and English (LTR) commands\n"
                "   • Automatic text direction: Persian = right-to-left, English = left-to-right\n"
                "   • Toggle language mode with ENGLISH/فارسی button (top-right)\n"
                "   • Shortcut: Ctrl+L to quickly switch languages\n\n"
                "📌 Available columns in lab_data.csv:\n"
                "   • id          (numeric)\n"
                "   • gender      (string: Male/Female)\n"
                "   • age         (numeric)\n"
                "   • glucose     (numeric - blood sugar)\n"
                "   • cholesterol (numeric)\n\n"
                "✅ Correct command execution order:\n"
                "   1. Load data:\n"
                "        LOAD \"lab_data.csv\" INTO df\n"
                "   2. Clean data:\n"
                "        CLEAN df DROP_DUPLICATES\n"
                "   3. Process & save:\n"
                "        SAVE df TO \"output.csv\""
            )
        else:
            help_text = (
                "راهنمای کامل کامپایلر زبان تخصصی فارسی/انگلیسی\n"
                "========================================\n\n"
                "📌 نکات مهم:\n"
                "   • این کامپایلر هر دو زبان فارسی (راست‌به‌چپ) و انگلیسی (چپ‌به‌راست) را پشتیبانی می‌کند\n"
                "   • جهت متن به‌صورت خودکار تنظیم می‌شود: فارسی = راست‌به‌چپ، انگلیسی = چپ‌به‌راست\n"
                "   • برای تغییر زبان، دکمه ENGLISH/فارسی را در گوشه بالا سمت راست بزنید\n"
                "   • میانبر: Ctrl+L برای تغییر سریع زبان\n\n"
                "📌 ستون‌های موجود در lab_data.csv:\n"
                "   • id          (عددی)\n"
                "   • gender      (رشته‌ای: Male/Female)\n"
                "   • age         (عددی)\n"
                "   • glucose     (عددی - قند خون)\n"
                "   • cholesterol (عددی)\n\n"
                "✅ ترتیب صحیح اجرای دستورات:\n"
                "   1. بارگذاری داده‌ها:\n"
                "        بگیر از \"lab_data.csv\" به نام df\n"
                "   2. پاکسازی داده‌ها:\n"
                "        پاکسازی df : حذف تکراری\n"
                "   3. پردازش و ذخیره:\n"
                "        ذخیره df : در \"خروجی.csv\""
            )
        messagebox.showinfo("Help Guide" if self.current_language == "en" else "راهنمای کامل", help_text)

    def compile_code(self):
        # Remove directional marks before compiling
        raw_code = self.input_text.get("1.0", tk.END)
        code = raw_code.replace(self.RLM, '').replace(self.LRM, '').strip()
        
        if not code:
            msg = "Please enter valid code to compile!" if self.current_language == "en" else "لطفاً کد معتبری برای کامپایل وارد کنید!"
            messagebox.showwarning("Empty Code" if self.current_language == "en" else "کد خالی", msg)
            return

        # Check for Persian typos (only in Persian mode)
        typo_suggestions = self.typo_suggester.check_typos(code)
        if typo_suggestions and self.current_language == "fa":
            warning_msg = "⚠️ Typo detected:\n\n" if self.current_language == "en" else "⚠️ اشتباه تایپی شناسایی شد:\n\n"
            for s in typo_suggestions:
                warning_msg += f"• {s['message']}\n"
            warning_msg += "\nContinue with compilation?" if self.current_language == "en" else "\nآیا می‌خواهید با این کد ادامه دهید؟"
            
            if not messagebox.askyesno("Confirm Compilation" if self.current_language == "en" else "تأیید کامپایل", warning_msg):
                return

        # Workflow enforcement - check for missing LOAD command
        has_load = re.search(r'بگیر از|LOAD.*INTO', code, re.IGNORECASE)
        has_operation = re.search(r'(پاکسازی|فیلتر|حذف_ستون|ذخیره|نمودار|ایجاد_ستون|CLEAN|FILTER|DROP_COL|SAVE|PLOT|CREATE_COL)', code, re.IGNORECASE)
        
        if has_operation and not has_load:
            msg = ("⚠️ Data not loaded!\n"
                   "Commands will fail without a LOAD statement.\n"
                   "Continue anyway?") if self.current_language == "en" else (
                   "⚠️ به نظر می‌رسد داده‌ها را بارگذاری نکرده‌اید!\n"
                   "بدون دستور «بگیر از»، سایر دستورات خطا می‌دهند.\n"
                   "آیا مطمئن هستید که می‌خواهید ادامه دهید؟")
            
            if not messagebox.askyesno("Execution Order Warning" if self.current_language == "en" else "هشدار ترتیب اجرا", msg):
                return

        # Update UI for compilation
        status_msg = "Compiling... please wait" if self.current_language == "en" else "در حال کامپایل... لطفاً صبر کنید"
        self.status_label.config(text=status_msg, fg=self.colors['secondary'])
        self.root.config(cursor="watch")
        self.root.update()

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        header_msg = "Executing code...\n" if self.current_language == "en" else "در حال اجرای کد...\n"
        self.output_text.insert(tk.END, header_msg, "header")
        self.output_text.insert(tk.END, "=" * 60 + "\n\n")
        self.output_text.config(state=tk.DISABLED)
        self.root.update()

        # Compile in background thread
        def compile_thread():
            success, output_log, error_msg = run_compiler(code, capture_output=True)
            self.root.after(0, lambda: self._update_output(success, output_log, error_msg, code))

        thread = threading.Thread(target=compile_thread, daemon=True)
        thread.start()

    def _update_output(self, success, output_log, error_msg, original_code):
        self.output_text.config(state=tk.NORMAL)

        if success:
            success_msg = "✓ Compilation and execution successful!\n" if self.current_language == "en" else "✓ کامپایل و اجرا با موفقیت انجام شد!\n"
            self.output_text.insert(tk.END, success_msg, "success")
            self.output_text.insert(tk.END, "=" * 60 + "\n\n")
            self.output_text.insert(tk.END, output_log)

            summary_msg = "\n" + "=" * 60 + "\nExecution Summary:\n" if self.current_language == "en" else "\n" + "=" * 60 + "\nخلاصه اجرا:\n"
            self.output_text.insert(tk.END, summary_msg, "header")
            
            paths = [
                "• Full report saved to output/report.txt\n",
                "• Plots saved to output/plots/\n",
                "• Processed data saved to processed_data.csv\n"
            ] if self.current_language == "en" else [
                "• گزارش کامل در پوشه output/report.txt ذخیره شد\n",
                "• نمودارها در پوشه output/plots/ ذخیره شدند\n",
                "• داده‌های پردازش شده در processed_data.csv ذخیره شدند\n"
            ]
            
            for path in paths:
                self.output_text.insert(tk.END, path, "path")
            self.output_text.insert(tk.END, "=" * 60 + "\n")
        else:
            error_header = "✗ Compilation or execution error:\n" if self.current_language == "en" else "✗ خطا در کامپایل یا اجرا:\n"
            self.output_text.insert(tk.END, error_header, "error")
            self.output_text.insert(tk.END, "=" * 60 + "\n\n")
            self.output_text.insert(tk.END, output_log)

            # Critical error: df not defined
            if "name 'df' is not defined" in error_msg or "name 'دیتافریم' is not defined" in error_msg:
                self.output_text.insert(tk.END, "\n!" * 60 + "\n", "critical")
                critical_msg = ("❗ CRITICAL ERROR: Data not loaded!\n"
                                "You're trying to operate on a DataFrame that doesn't exist.\n\n"
                                "✅ Solution:\n"
                                "Always start with a LOAD command:\n"
                                "  LOAD \"lab_data.csv\" INTO df\n"
                                "  or\n"
                                "  بگیر از \"lab_data.csv\" به نام df") if self.current_language == "en" else (
                                "❗ خطای بحرانی: داده‌ها بارگذاری نشده‌اند!\n"
                                "این خطا به این دلیل رخ داده که شما سعی کرده‌اید روی دیتافریمی کار کنید که هنوز ساخته نشده است.\n\n"
                                "✅ راه‌حل:\n"
                                "همیشه اولین دستور باید بارگذاری داده‌ها باشد:\n"
                                "  بگیر از \"lab_data.csv\" به نام df\n"
                                "  یا\n"
                                "  LOAD \"lab_data.csv\" INTO df")
                self.output_text.insert(tk.END, critical_msg, "critical")
                self.output_text.insert(tk.END, "\n!" * 60 + "\n", "critical")

            # Column name error
            if ("رمز_ملی" in original_code or "national_id" in original_code) and "KeyError" in error_msg:
                warning_msg = ("\n⚠️ Invalid column name:\n"
                               "Column 'national_id' does not exist in lab_data.csv!\n"
                               "Valid columns in this file:\n"
                               "  id, gender, age, glucose, cholesterol\n\n"
                               "To drop a column, use one of the above:\n"
                               "  DROP_COL df id\n"
                               "  or\n"
                               "  حذف_ستون df : id") if self.current_language == "en" else (
                               "\n⚠️ هشدار ستون نامعتبر:\n"
                               "ستون «رمز_ملی» در فایل lab_data.csv وجود ندارد!\n"
                               "ستون‌های معتبر در این فایل:\n"
                               "  id, gender, age, glucose, cholesterol\n\n"
                               "برای حذف ستون، از یکی از ستون‌های بالا استفاده کنید:\n"
                               "  حذف_ستون df : id\n"
                               "  یا\n"
                               "  DROP_COL df id")
                self.output_text.insert(tk.END, warning_msg, "warning")

            # Show Persian typos if detected
            typo_suggestions = self.typo_suggester.check_typos(original_code)
            if typo_suggestions:
                typo_header = "\n⚠️ Typo suggestions:\n" if self.current_language == "en" else "\n⚠️ اشتباهات تایپی در کد شما:\n"
                self.output_text.insert(tk.END, typo_header, "warning")
                for s in typo_suggestions:
                    self.output_text.insert(tk.END, f"  • {s['message']}\n", "warning")

        self.output_text.config(state=tk.DISABLED)

        # Update status bar
        if success:
            status_msg = "✓ Execution successful | Results saved to output/ and processed_data.csv" if self.current_language == "en" else "✓ اجرا موفقیت‌آمیز | نتایج در output/ و processed_data.csv ذخیره شدند"
            self.status_label.config(text=status_msg, fg=self.colors['success'])
            
            success_title = "Success" if self.current_language == "en" else "موفقیت"
            success_msg = ("Code executed successfully!\n\n"
                          "• Full report shown in output panel\n"
                          "• Plots saved to output/plots/\n"
                          "• Processed data saved to processed_data.csv") if self.current_language == "en" else (
                          "اجرای کد با موفقیت کامل شد!\n\n"
                          "• گزارش کامل در پنل خروجی نمایش داده شد\n"
                          "• نمودارها در پوشه output/plots ذخیره شدند\n"
                          "• داده‌های پردازش شده در processed_data.csv ذخیره شدند")
            messagebox.showinfo(success_title, success_msg)
        else:
            status_msg = "✗ Execution failed - see details in output panel" if self.current_language == "en" else "✗ خطا در اجرا - جزئیات کامل در پنل خروجی"
            self.status_label.config(text=status_msg, fg=self.colors['danger'])
            
            error_title = "Execution Error" if self.current_language == "en" else "خطا در اجرا"
            short_error = error_msg.split('\n')[0] if '\n' in error_msg else error_msg[:150]
            messagebox.showerror(error_title, f"Error:\n{short_error}...")

        self.root.config(cursor="")

    # === EVENT HANDLERS ===
    def _on_arrow_key(self, event):
        if self.suggestion_popup.visible:
            direction = "up" if event.keysym == "Up" else "down"
            if self.suggestion_popup.navigate(direction):
                return "break"
        return None

    def _on_enter_key(self, event):
        if self.suggestion_popup.visible and self.suggestion_popup.popup and self.suggestion_popup.popup.winfo_exists():
            index = self.suggestion_popup.get_selected_index()
            self.on_suggestion_selected(index)
            self.suggestion_popup.hide()
            self.input_text.focus_set()
            return "break"
        return None

    def _on_key_press(self, event):
        navigation_keys = ('Up', 'Down', 'Return', 'Tab', 'Escape', 'Left', 'Right', 'Control_L', 'Control_R')
        if event.keysym not in navigation_keys:
            self.suggestion_popup.hide()
        self.input_text.focus_set()
        return None

    def _on_key_release(self, event):
        # Enforce correct text direction based on language mode AFTER every keystroke
        if self.current_language == "fa":
            self.input_text.tag_add("rtl", "1.0", "end")
            self.input_text.configure(font=(self.base_font, 12))
        else:
            self.input_text.tag_add("ltr", "1.0", "end")
            self.input_text.configure(font=(self.en_font, 12))

        ignore_keys = ('Return', 'Tab', 'Escape', 'BackSpace', 'Delete', 'Left', 'Right',
                      'Up', 'Down', 'Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R')
        if event.keysym in ignore_keys:
            return

        if self.suggestion_timer:
            self.root.after_cancel(self.suggestion_timer)

        self.suggestion_timer = self.root.after(250, self._show_suggestions)

    def _on_mouse_click(self, event):
        self.suggestion_popup.hide()

    def _show_suggestions(self):
        if self.root.focus_get() != self.input_text:
            return

        cursor_pos = self.input_text.index(tk.INSERT)
        all_text = self.input_text.get("1.0", tk.END)
        char_index = self._get_char_index(cursor_pos)
        text_up_to_cursor = all_text[:char_index]

        if self._is_inside_string(text_up_to_cursor):
            self.suggestion_popup.hide()
            return

        suggestions = self.suggestion_engine.get_suggestions(text_up_to_cursor, char_index, self.current_language)

        if suggestions:
            bbox = self.input_text.bbox(cursor_pos)
            if bbox:
                x, y, width, height = bbox
                screen_x = self.input_text.winfo_rootx() + x

                # Position popup based on language direction
                if self.current_language == "fa":
                    popup_x = screen_x - 430
                else:
                    popup_x = screen_x + 25

                popup_y = self.input_text.winfo_rooty() + y + height + 8

                screen_width = self.root.winfo_screenwidth()
                if popup_x < 15:
                    popup_x = 15
                elif popup_x + 450 > screen_width:
                    popup_x = screen_width - 455

                self.suggestion_popup.show(suggestions, popup_x, popup_y, self.current_language)
        else:
            self.suggestion_popup.hide()

    def on_suggestion_selected(self, index):
        cursor_pos = self.input_text.index(tk.INSERT)
        line_num, char_num = map(int, cursor_pos.split('.'))
        text_before = self.input_text.get(f"{line_num}.0", cursor_pos)

        last_space = max(text_before.rfind(' '), text_before.rfind('\n'))

        all_text = self.input_text.get("1.0", tk.END)
        char_index = self._get_char_index(cursor_pos)
        text_up_to_cursor = all_text[:char_index]
        suggestions = self.suggestion_engine.get_suggestions(text_up_to_cursor, char_index, self.current_language)

        if index < len(suggestions):
            keyword, templates = suggestions[index]
            template, cursor_hint = templates[0]

            if last_space != -1 and text_before[last_space:].strip():
                start_pos = f"{line_num}.{last_space + 1}"
            else:
                start_pos = f"{line_num}.0"

            self.input_text.delete(start_pos, cursor_pos)
            self.input_text.insert(start_pos, template + "  ")

            # Position cursor appropriately
            new_cursor_pos = start_pos
            template_text = template

            if cursor_hint == "quote":
                first_quote = template_text.find('"')
                if first_quote != -1:
                    next_quote = template_text.find('"', first_quote + 1)
                    if next_quote != -1:
                        offset = first_quote + 1
                        col_offset = int(start_pos.split('.')[1])
                        new_cursor_pos = f"{line_num}.{col_offset + offset}"

            elif cursor_hint == "colon":
                colon_pos = template_text.find(':')
                if colon_pos != -1:
                    offset = colon_pos + 2
                    col_offset = int(start_pos.split('.')[1])
                    new_cursor_pos = f"{line_num}.{col_offset + offset}"

            else:
                offset = len(template_text) + 1
                col_offset = int(start_pos.split('.')[1])
                new_cursor_pos = f"{line_num}.{col_offset + offset}"

            self.input_text.mark_set(tk.INSERT, new_cursor_pos)
            self.input_text.see(tk.INSERT)
            
            # Reapply text direction tag after insertion
            if self.current_language == "fa":
                self.input_text.tag_add("rtl", "1.0", "end")
                self.input_text.configure(font=(self.base_font, 12))
            else:
                self.input_text.tag_add("ltr", "1.0", "end")
                self.input_text.configure(font=(self.en_font, 12))

        self.input_text.focus_set()
        self.suggestion_popup.hide()

    def _get_char_index(self, text_index):
        line, char = map(int, text_index.split('.'))
        text = self.input_text.get("1.0", tk.END)
        lines = text.split('\n')
        return sum(len(l) + 1 for l in lines[:line-1]) + char

    def _is_inside_string(self, text):
        quote_count = text.count('"')
        return quote_count % 2 == 1

    def _is_persian_text(self, text):
        return any('\u0600' <= c <= '\u06FF' for c in text)

if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    root = tk.Tk()

    try:
        root.tk.call('tk', 'scaling', 1.25)
    except:
        pass

    app = PersianCompilerGUI(root)

    def on_closing():
        msg = "Exit application?\nUnsaved changes will be lost." if app.current_language == "en" else "آیا می‌خواهید از برنامه خارج شوید؟\nتغییرات ذخیره نشده از بین خواهند رفت"
        if messagebox.askokcancel("Exit" if app.current_language == "en" else "خروج", msg):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()