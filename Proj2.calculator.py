import ast
import math
import operator
import re
import tkinter as tk
from datetime import date, datetime, timedelta


class CalculatorError(Exception):
    """Raised when an expression is not supported or cannot be evaluated."""


# --------------------------------------------------------------------------
# Expression evaluator (safe: uses ast, never eval)
# --------------------------------------------------------------------------
def evaluate_expression(expression, angle_mode):
    binary_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unary_operators = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    angle = math.radians if angle_mode == "DEG" else float
    inverse_angle = math.degrees if angle_mode == "DEG" else float
    functions = {
        "sin": lambda value: math.sin(angle(value)),
        "cos": lambda value: math.cos(angle(value)),
        "tan": lambda value: math.tan(angle(value)),
        "asin": lambda value: inverse_angle(math.asin(value)),
        "acos": lambda value: inverse_angle(math.acos(value)),
        "atan": lambda value: inverse_angle(math.atan(value)),
        "log": math.log10,
        "abs": abs,
        "exp": math.exp,
        "fact": math.factorial,
    }
    constants = {"pi": math.pi, "e": math.e}

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except (SyntaxError, ValueError) as error:
        raise CalculatorError("Check the expression") from error

    def calculate(node):
        if isinstance(node, ast.Expression):
            return calculate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and node.id in constants:
            return constants[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operators:
            return unary_operators[type(node.op)](calculate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in binary_operators:
            left = calculate(node.left)
            right = calculate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise CalculatorError("Exponent is too large")
            return binary_operators[type(node.op)](left, right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function = functions.get(node.func.id)
            if function is None or node.keywords or len(node.args) != 1:
                raise CalculatorError("Unsupported function")
            value = calculate(node.args[0])
            if node.func.id == "fact":
                if value < 0 or int(value) != value or value > 170:
                    raise CalculatorError("Factorial needs an integer from 0 to 170")
                value = int(value)
            return function(value)
        raise CalculatorError("Unsupported expression")

    result = calculate(tree)
    if isinstance(result, complex) or not math.isfinite(result):
        raise CalculatorError("Result is outside the supported range")
    return result


# --------------------------------------------------------------------------
# Helpers for the fitness / finance tools
# --------------------------------------------------------------------------
def inr(amount):
    """Format a number in Indian rupee style, e.g. ₹12,34,567.00"""
    sign = "-" if amount < 0 else ""
    whole, frac = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        whole = f"{head},{tail}"
    return f"{sign}₹{whole}.{frac}"


def _num(raw, name, minimum=0.0, strict=True):
    try:
        value = float(str(raw).replace(",", "").strip())
    except ValueError:
        raise ValueError(f"{name}: sahi number daalo")
    if (strict and value <= minimum) or (not strict and value < minimum):
        word = "se bada" if strict else "ya usse barabar/bada"
        raise ValueError(f"{name} {minimum:g} {word} hona chahiye")
    return value


def _gender(raw):
    letter = str(raw).strip().lower()[:1]
    if letter not in ("m", "f"):
        raise ValueError("Gender: m ya f likho")
    return letter


# ---- Fitness tools -------------------------------------------------------
def calc_bmi(v):
    weight = _num(v[0], "Weight")
    height_cm = _num(v[1], "Height")
    if not 50 <= height_cm <= 250:
        raise ValueError("Height 50 se 250 cm ke beech hona chahiye")
    h = height_cm / 100
    bmi = weight / (h * h)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    details = f"Healthy weight range: {18.5 * h * h:.1f} - {24.9 * h * h:.1f} kg"
    return f"BMI {bmi:.1f}  ({category})", details, round(bmi, 1)


def calc_bmr(v):
    weight = _num(v[0], "Weight")
    height = _num(v[1], "Height")
    age = _num(v[2], "Age")
    gender = _gender(v[3])
    activity = _num(v[4], "Activity", minimum=1.0, strict=False)
    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == "m" else -161)
    tdee = bmr * activity
    details = (
        f"Maintenance (TDEE): {tdee:.0f} kcal/day\n"
        f"Weight loss ke liye: ~{max(tdee - 500, 0):.0f} kcal/day\n"
        f"Weight gain ke liye: ~{tdee + 300:.0f} kcal/day"
    )
    return f"BMR {bmr:.0f} kcal/day", details, round(bmr)


def calc_water(v):
    weight = _num(v[0], "Weight")
    minutes = _num(v[1], "Exercise", minimum=0, strict=False)
    liters = weight * 0.033 + (minutes / 30) * 0.35
    glasses = liters / 0.25
    return f"Water: {liters:.1f} litre/day", f"~{glasses:.0f} glass (250 ml each)", round(liters, 1)


def calc_ideal_weight(v):
    height_cm = _num(v[0], "Height")
    gender = _gender(v[1])
    inches = height_cm / 2.54
    base = 50.0 if gender == "m" else 45.5
    ideal = base + 2.3 * max(0.0, inches - 60)
    return f"Ideal weight: {ideal:.1f} kg", f"Range (±10%): {ideal * 0.9:.1f} - {ideal * 1.1:.1f} kg  (Devine formula)", round(ideal, 1)


def calc_heart(v):
    age = _num(v[0], "Age")
    if age > 120:
        raise ValueError("Age 120 se kam honi chahiye")
    top = 220 - age
    zones = [("Warm-up", 0.50, 0.60), ("Fat burn", 0.60, 0.70), ("Cardio", 0.70, 0.85), ("Peak", 0.85, 1.00)]
    lines = [f"{name}: {round(top * a)} - {round(top * b)} bpm" for name, a, b in zones]
    return f"Max heart rate: {top:.0f} bpm", "\n".join(lines), round(top)


# ---- Finance tools -------------------------------------------------------
def calc_emi(v):
    principal = _num(v[0], "Loan amount")
    rate = _num(v[1], "Interest rate", minimum=0, strict=False)
    months = int(_num(v[2], "Tenure"))
    r = rate / 1200
    if r == 0:
        emi = principal / months
    else:
        growth = (1 + r) ** months
        emi = principal * r * growth / (growth - 1)
    total = emi * months
    details = f"Total payment: {inr(total)}\nTotal interest: {inr(total - principal)}"
    return f"EMI: {inr(emi)} / month", details, round(emi, 2)


def calc_simple_interest(v):
    principal = _num(v[0], "Principal")
    rate = _num(v[1], "Rate", minimum=0, strict=False)
    years = _num(v[2], "Time")
    interest = principal * rate * years / 100
    return f"Simple Interest: {inr(interest)}", f"Total amount: {inr(principal + interest)}", round(interest, 2)


def calc_compound_interest(v):
    principal = _num(v[0], "Principal")
    rate = _num(v[1], "Rate", minimum=0, strict=False)
    years = _num(v[2], "Time")
    n = int(_num(v[3], "Compounds/year"))
    amount = principal * (1 + rate / (100 * n)) ** (n * years)
    return f"Compound Interest: {inr(amount - principal)}", f"Total amount: {inr(amount)}", round(amount - principal, 2)


def calc_gst(v):
    amount = _num(v[0], "Amount")
    rate = _num(v[1], "GST rate", minimum=0, strict=False)
    mode = str(v[2]).strip().lower()[:1]
    if mode not in ("a", "r"):
        raise ValueError("Mode: a (GST add) ya r (GST remove) likho")
    if mode == "a":
        gst = amount * rate / 100
        base, total = amount, amount + gst
    else:
        base = amount / (1 + rate / 100)
        gst = amount - base
        total = amount
    details = (
        f"Base price: {inr(base)}\nGST: {inr(gst)}  (CGST {inr(gst / 2)} + SGST {inr(gst / 2)})"
    )
    return f"Total: {inr(total)}", details, round(total, 2)


def calc_sip(v):
    monthly = _num(v[0], "Monthly SIP")
    rate = _num(v[1], "Return rate", minimum=0, strict=False)
    years = _num(v[2], "Years")
    n = round(years * 12)
    if n < 1:
        raise ValueError("Years kam se kam 1 mahina (0.1) hone chahiye")
    i = rate / 1200
    future = monthly * n if i == 0 else monthly * (((1 + i) ** n - 1) / i) * (1 + i)
    invested = monthly * n
    details = f"Invested: {inr(invested)}\nGain: {inr(future - invested)}"
    return f"Maturity value: {inr(future)}", details, round(future, 2)


# ---- Age calculator ------------------------------------------------------
def _parse_date(raw, name):
    text = str(raw).strip().lower()
    if text in ("today", "aaj", ""):
        return date.today()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %m %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"{name}: date DD-MM-YYYY format mein likho (jaise 15-08-2000)")


def calc_age(v):
    dob = _parse_date(v[0], "Date of birth")
    today = _parse_date(v[1], "As-on date")
    if dob > today:
        raise ValueError("Date of birth, as-on date se pehle honi chahiye")

    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day
    if days < 0:
        months -= 1
        days += (today.replace(day=1) - timedelta(days=1)).day
    if months < 0:
        years -= 1
        months += 12

    try:
        next_birthday = dob.replace(year=today.year)
    except ValueError:  # born on 29 Feb
        next_birthday = date(today.year, 3, 1)
    if next_birthday < today:
        try:
            next_birthday = dob.replace(year=today.year + 1)
        except ValueError:
            next_birthday = date(today.year + 1, 3, 1)
    days_left = (next_birthday - today).days
    birthday_line = "Aaj aapka birthday hai!" if days_left == 0 else f"Next birthday: {days_left} din baad ({next_birthday.strftime('%d %b %Y')})"

    total_days = (today - dob).days
    details = (
        f"Total months: {years * 12 + months:,}\n"
        f"Total weeks: {total_days // 7:,}\n"
        f"Total days: {total_days:,}\n"
        f"Born on: {dob.strftime('%A')}\n"
        f"{birthday_line}"
    )
    return f"{years} saal, {months} mahine, {days} din", details, years


FITNESS_TOOLS = [
    {"title": "BMI Calculator", "short": "BMI", "compute": calc_bmi,
     "fields": [("Weight (kg)", "70"), ("Height (cm)", "170")]},
    {"title": "BMR & Daily Calories", "short": "BMR", "compute": calc_bmr,
     "fields": [("Weight (kg)", "70"), ("Height (cm)", "170"), ("Age (years)", "25"),
                ("Gender (m/f)", "m"), ("Activity (1.2 - 1.9)", "1.2")]},
    {"title": "Daily Water Intake", "short": "Water", "compute": calc_water,
     "fields": [("Weight (kg)", "70"), ("Exercise (min/day)", "0")]},
    {"title": "Ideal Weight", "short": "Ideal Wt", "compute": calc_ideal_weight,
     "fields": [("Height (cm)", "170"), ("Gender (m/f)", "m")]},
    {"title": "Heart Rate Zones", "short": "Heart", "compute": calc_heart,
     "fields": [("Age (years)", "25")]},
]

FINANCE_TOOLS = [
    {"title": "EMI Calculator", "short": "EMI", "compute": calc_emi,
     "fields": [("Loan amount (₹)", "500000"), ("Interest rate (% / year)", "9"), ("Tenure (months)", "60")]},
    {"title": "Simple Interest", "short": "Simple Int", "compute": calc_simple_interest,
     "fields": [("Principal (₹)", "100000"), ("Rate (% / year)", "8"), ("Time (years)", "3")]},
    {"title": "Compound Interest", "short": "Comp Int", "compute": calc_compound_interest,
     "fields": [("Principal (₹)", "100000"), ("Rate (% / year)", "8"), ("Time (years)", "3"),
                ("Compounds per year", "1")]},
    {"title": "GST Calculator", "short": "GST", "compute": calc_gst,
     "fields": [("Amount (₹)", "1000"), ("GST rate (%)", "18"), ("Mode (a = add, r = remove)", "a")]},
    {"title": "SIP Calculator", "short": "SIP", "compute": calc_sip,
     "fields": [("Monthly SIP (₹)", "5000"), ("Expected return (% / year)", "12"), ("Years", "10")]},
]

UTILITY_TOOLS = [
    {"title": "Age Calculator", "short": "Age", "compute": calc_age,
     "fields": [("Date of birth (DD-MM-YYYY)", "01-01-2000"),
                ("As on date (DD-MM-YYYY / today)", "today")]},
]


# --------------------------------------------------------------------------
# Tool dialog (fully keyboard driven)
# --------------------------------------------------------------------------
class ToolDialog(tk.Toplevel):
    def __init__(self, app, tool):
        super().__init__(app.root)
        self.app = app
        self.tool = tool
        self.value = None
        colors = app.COLORS

        self.title(tool["title"])
        self.configure(bg=colors["background"])
        self.resizable(False, False)
        self.transient(app.root)
        self.geometry(f"+{app.root.winfo_x() + 30}+{app.root.winfo_y() + 60}")

        body = tk.Frame(self, bg=colors["background"], padx=22, pady=18)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=tool["title"].upper(), bg=colors["background"], fg=colors["accent"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(body, text="Enter = Calculate   |   Ctrl+Enter = Calculator mein daalo   |   Esc = Band",
                 bg=colors["background"], fg=colors["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 12))

        form = tk.Frame(body, bg=colors["background"])
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)
        self.entries = []
        for row, (label, default) in enumerate(tool["fields"]):
            tk.Label(form, text=label, bg=colors["background"], fg=colors["text"],
                     font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 14))
            entry = tk.Entry(form, bg=colors["key"], fg=colors["text"], insertbackground=colors["text"],
                             relief="flat", font=("Segoe UI", 12), justify="right", width=16,
                             highlightthickness=1, highlightbackground=colors["panel"],
                             highlightcolor=colors["accent"])
            entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="ew", ipady=4)
            entry.bind("<Return>", lambda e: (self.calculate(), "break")[1])
            entry.bind("<KP_Enter>", lambda e: (self.calculate(), "break")[1])
            entry.bind("<Control-Return>", lambda e: (self.insert_and_close(), "break")[1])
            entry.bind("<Down>", lambda e, i=row: self._move(i + 1))
            entry.bind("<Up>", lambda e, i=row: self._move(i - 1))
            entry.bind("<FocusIn>", lambda e: e.widget.after(1, lambda w=e.widget: w.select_range(0, tk.END)))
            self.entries.append(entry)

        self.headline = tk.StringVar(value="")
        self.details = tk.StringVar(value="")
        result = tk.Frame(body, bg=colors["panel"], padx=14, pady=12)
        result.pack(fill="x", pady=(14, 10))
        tk.Label(result, textvariable=self.headline, bg=colors["panel"], fg=colors["accent"],
                 font=("Segoe UI", 13, "bold"), anchor="w", justify="left", wraplength=360).pack(fill="x")
        tk.Label(result, textvariable=self.details, bg=colors["panel"], fg=colors["text"],
                 font=("Segoe UI", 10), anchor="w", justify="left", wraplength=360).pack(fill="x", pady=(6, 0))

        buttons = tk.Frame(body, bg=colors["background"])
        buttons.pack(fill="x")
        for text, command, bg, fg in [
            ("Calculate", self.calculate, colors["accent"], colors["background"]),
            ("Calculator mein daalo", self.insert_and_close, colors["key"], colors["text"]),
            ("Close", self.close, colors["panel"], colors["danger"]),
        ]:
            tk.Button(buttons, text=text, command=command, bg=bg, fg=fg, relief="flat", bd=0,
                      activebackground=colors["key_hover"], activeforeground=colors["text"],
                      font=("Segoe UI", 10, "bold"), padx=12, pady=6, cursor="hand2",
                      takefocus=False).pack(side="left", padx=(0, 8))

        self.bind("<Escape>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.update_idletasks()
        self.grab_set()
        self.entries[0].focus_set()
        self.calculate()

    def _move(self, index):
        index = max(0, min(len(self.entries) - 1, index))
        self.entries[index].focus_set()
        return "break"

    def calculate(self):
        try:
            headline, details, value = self.tool["compute"]([e.get() for e in self.entries])
        except (ValueError, ArithmeticError) as error:
            self.headline.set(str(error) or "Math error")
            self.details.set("")
            self.value = None
            return False
        self.headline.set(headline)
        self.details.set(details)
        self.value = value
        return True

    def insert_and_close(self):
        if self.calculate() and self.value is not None:
            self.app.insert_value(self.value)
            self.close()

    def close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        self.app.root.focus_set()


# --------------------------------------------------------------------------
# Main calculator window
# --------------------------------------------------------------------------
class ScientificCalculator:
    COLORS = {
        "background": "#11191a",
        "panel": "#1b2728",
        "key": "#293738",
        "key_hover": "#354748",
        "text": "#edf4ef",
        "muted": "#8fa3a0",
        "accent": "#50d8b5",
        "operator": "#d4a76a",
        "danger": "#e48678",
    }
    # Keys that continue working on the previous result instead of starting fresh
    CONTINUE = {"+", "-", "*", "/", "^", "%", "//", "**2", "percent"}

    def __init__(self, root):
        self.root = root
        self.root.title("Scientific Calculator")
        self.root.geometry("470x860")
        self.root.minsize(400, 300)
        self.root.configure(bg=self.COLORS["background"])
        self.expression = ""
        self.just_calculated = False
        self.history_items = []
        self.history_index = -1
        self.tool_window = None
        self.angle_mode = tk.StringVar(value="DEG")
        self.display = tk.StringVar(value="0")
        self.result = tk.StringVar(value="Ready")
        # Show / hide state (like the "more" arrow on phone calculators)
        self.view = {"sci": True, "tools": True, "hist": True}
        self.view_buttons = {}
        self.sci_widgets = []

        self._build_ui()
        self._bind_keys()
        self._apply_view()
        self.root.focus_set()

    # ---- UI ------------------------------------------------------------
    def _build_ui(self):
        colors = self.COLORS
        container = tk.Frame(self.root, bg=colors["background"], padx=18, pady=14)
        container.pack(fill="both", expand=True)

        header = tk.Frame(container, bg=colors["background"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="CALCULATOR", bg=colors["background"],
                 fg=colors["muted"], font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(
            header, textvariable=self.angle_mode, command=self._toggle_angle_mode,
            bg=colors["panel"], fg=colors["accent"], activebackground=colors["key_hover"],
            activeforeground=colors["accent"], relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), padx=12, pady=4, cursor="hand2", takefocus=False,
        ).pack(side="right")
        for key, text in (("hist", "HIST"), ("tools", "TOOLS"), ("sci", "SCI")):
            toggle = tk.Button(
                header, text=text, command=lambda k=key: self._toggle_view(k),
                bg=colors["panel"], fg=colors["accent"], activebackground=colors["key_hover"],
                activeforeground=colors["accent"], relief="flat", bd=0,
                font=("Segoe UI", 8, "bold"), padx=8, pady=6, cursor="hand2", takefocus=False,
            )
            toggle.pack(side="right", padx=(0, 6))
            self.view_buttons[key] = toggle

        screen = tk.Frame(container, bg=colors["panel"], padx=16, pady=10)
        screen.pack(fill="x", pady=(0, 10))
        tk.Label(screen, textvariable=self.display, anchor="e", bg=colors["panel"],
                 fg=colors["text"], font=("Segoe UI", 20), height=1).pack(fill="x")
        tk.Label(screen, textvariable=self.result, anchor="e", bg=colors["panel"],
                 fg=colors["accent"], font=("Segoe UI", 16, "bold"), height=1).pack(fill="x")

        # (label, value, columnspan)
        keys = [
            [("sin", "sin(", 1), ("cos", "cos(", 1), ("tan", "tan(", 1),
             ("asin", "asin(", 1), ("acos", "acos(", 1), ("atan", "atan(", 1)],
            [("x²", "**2", 1), ("log", "log(", 1), ("abs", "abs(", 1),
             ("fact", "fact(", 1), ("exp", "exp(", 1), ("π", "pi", 1)],
            [("C", "clear", 1), ("DEL", "delete", 1), ("(", "(", 1),
             (")", ")", 1), ("%", "percent", 1), ("÷", "/", 1)],
            [("7", "7", 1), ("8", "8", 1), ("9", "9", 1), ("×", "*", 1), ("^", "^", 1), ("e", "e", 1)],
            [("4", "4", 1), ("5", "5", 1), ("6", "6", 1), ("−", "-", 1), ("mod", "%", 1), ("//", "//", 1)],
            [("1", "1", 1), ("2", "2", 1), ("3", "3", 1), ("+", "+", 1), ("±", "negate", 1), ("00", "00", 1)],
            [("0", "0", 2), (".", ".", 1), ("=", "equals", 3)],
        ]
        keypad = tk.Frame(container, bg=colors["background"])
        keypad.pack(fill="x")
        self.keypad = keypad
        for column in range(6):
            keypad.grid_columnconfigure(column, weight=1, uniform="key")
        operator_values = {"/", "*", "-", "+", "^", "%", "//", "percent", "**2"}
        for row_index, row in enumerate(keys):
            keypad.grid_rowconfigure(row_index, weight=1, minsize=40)
            column_index = 0
            for label, value, span in row:
                is_action = value in {"clear", "delete", "equals"}
                background = colors["accent"] if value == "equals" else (
                    colors["panel"] if is_action else colors["key"])
                foreground = colors["background"] if value == "equals" else (
                    colors["danger"] if value == "clear" else (
                        colors["operator"] if value in operator_values else colors["text"]))
                key_button = tk.Button(
                    keypad, text=label, command=lambda item=value: self._press(item),
                    bg=background, fg=foreground, activebackground=colors["key_hover"],
                    activeforeground=colors["text"], relief="flat", bd=0,
                    font=("Segoe UI", 10 if len(label) > 2 else 12, "bold"),
                    cursor="hand2", takefocus=False,
                )
                key_button.grid(row=row_index, column=column_index, columnspan=span,
                                sticky="nsew", padx=2, pady=2)
                if row_index < 2:  # sin/cos/... and x²/log/... rows
                    self.sci_widgets.append(key_button)
                column_index += span

        self.tools_frame = tk.Frame(container, bg=colors["background"])
        self._build_tool_row(self.tools_frame, "FITNESS", FITNESS_TOOLS, "12345")
        self._build_tool_row(self.tools_frame, "FINANCE", FINANCE_TOOLS, "67890")
        self._build_tool_row(self.tools_frame, "OTHER", UTILITY_TOOLS, "A")

        self.history_frame = tk.Frame(container, bg=colors["background"])
        history_header = tk.Frame(self.history_frame, bg=colors["background"])
        history_header.pack(fill="x", pady=(8, 3))
        tk.Label(history_header, text="HISTORY   (Up / Down = recall)", bg=colors["background"],
                 fg=colors["muted"], font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Button(history_header, text="Clear", command=self._clear_history,
                  bg=colors["background"], fg=colors["muted"], activebackground=colors["background"],
                  activeforeground=colors["text"], relief="flat", bd=0, cursor="hand2",
                  takefocus=False).pack(side="right")
        self.history = tk.Listbox(
            self.history_frame, height=3, bg=colors["panel"], fg=colors["muted"],
            selectbackground=colors["key_hover"], selectforeground=colors["text"],
            relief="flat", bd=0, font=("Segoe UI", 10), activestyle="none",
            takefocus=False, exportselection=False,
        )
        self.history.pack(fill="both", expand=True)
        self.history.bind("<<ListboxSelect>>", self._recall_history_click)

    # ---- Show / hide sections -------------------------------------------
    def _toggle_view(self, key):
        self.view[key] = not self.view[key]
        self._apply_view()
        self.root.focus_set()
        return "break"

    def _apply_view(self):
        colors = self.COLORS
        # Scientific rows (rows 0 and 1 of the keypad)
        for row in (0, 1):
            self.keypad.grid_rowconfigure(row, minsize=40 if self.view["sci"] else 0)
        for widget in self.sci_widgets:
            if self.view["sci"]:
                widget.grid()
            else:
                widget.grid_remove()
        # Tools and history sections (repacked in order so the layout stays correct)
        self.tools_frame.pack_forget()
        self.history_frame.pack_forget()
        if self.view["tools"]:
            self.tools_frame.pack(fill="x")
        if self.view["hist"]:
            self.history_frame.pack(fill="both", expand=True)
        # Toggle buttons look bright when the section is visible, dim when hidden
        for key, button in self.view_buttons.items():
            if self.view[key]:
                button.configure(bg=colors["panel"], fg=colors["accent"])
            else:
                button.configure(bg=colors["background"], fg=colors["muted"])
        self._fit_window()

    def _fit_window(self):
        self.root.update_idletasks()
        height = self.root.winfo_reqheight()
        width = self.root.winfo_width()
        if width < 400:  # window not mapped yet
            width = 470
        self.root.minsize(400, height)
        self.root.geometry(f"{width}x{height}")

    def _build_tool_row(self, parent, title, tools, shortcut_keys):
        colors = self.COLORS
        tk.Label(parent, text=f"{title}   (Ctrl + {' / '.join(shortcut_keys)})", bg=colors["background"],
                 fg=colors["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
        row = tk.Frame(parent, bg=colors["background"])
        row.pack(fill="x")
        for column in range(5):
            row.grid_columnconfigure(column, weight=1, uniform="tool")
        for column, (tool, key) in enumerate(zip(tools, shortcut_keys)):
            row.grid_columnconfigure(column, weight=1, uniform="tool")
            tk.Button(
                row, text=f"{tool['short']}\nCtrl+{key}", command=lambda t=tool: self.open_tool(t),
                bg=colors["panel"], fg=colors["accent"], activebackground=colors["key_hover"],
                activeforeground=colors["accent"], relief="flat", bd=0,
                font=("Segoe UI", 8, "bold"), cursor="hand2", takefocus=False, pady=3,
            ).grid(row=0, column=column, sticky="nsew", padx=2)

    # ---- Keyboard ------------------------------------------------------
    def _bind_keys(self):
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Control-c>", self._copy_result)
        self.root.bind("<Control-v>", self._paste)
        all_tools = list(zip("1234567890", FITNESS_TOOLS + FINANCE_TOOLS))
        for key, tool in all_tools:
            self.root.bind(f"<Control-Key-{key}>", lambda e, t=tool: (self.open_tool(t), "break")[1])
        for key in ("a", "A"):
            self.root.bind(f"<Control-{key}>", lambda e: (self.open_tool(UTILITY_TOOLS[0]), "break")[1])
        for letter, view_key in (("s", "sci"), ("t", "tools"), ("h", "hist")):
            for char in (letter, letter.upper()):
                self.root.bind(f"<Control-{char}>", lambda e, k=view_key: self._toggle_view(k))

    def _on_key(self, event):
        if event.state & 0x4:  # Ctrl is held: leave to the Ctrl shortcuts
            return None
        keysym = event.keysym
        if keysym in {"Return", "KP_Enter"}:
            self._calculate()
            return "break"
        if keysym in {"Escape", "Delete"}:
            self._press("clear")
            return "break"
        if keysym == "BackSpace":
            self._press("delete")
            return "break"
        if keysym == "Tab":
            self._toggle_angle_mode()
            return "break"
        if keysym == "Up":
            self._history_step(+1)
            return "break"
        if keysym == "Down":
            self._history_step(-1)
            return "break"

        char = event.char
        if not char:
            return None
        if char in "0123456789.+-*/()":
            self._press(char)
        elif char == "%":
            self._press("percent")
        elif char == "^":
            self._press("^")
        elif char == "=":
            self._calculate()
        elif char.lower() == "m":
            self._press("%")  # mod
        elif char.isascii() and char.isalpha():
            self._press(char.lower())  # lets you type sin(, cos(, pi, fact( ...
        else:
            return None
        return "break"

    def _copy_result(self, _event=None):
        text = self.expression or ""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.result.set("Copied")
        return "break"

    def _paste(self, _event=None):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        cleaned = re.sub(r"[^0-9a-zA-Z.+\-*/()%^]", "", text).lower().replace("^", "**")
        if cleaned:
            if self.just_calculated:
                self.expression = ""
            self.expression += cleaned
            self.just_calculated = False
            self._refresh_display()
        return "break"

    # ---- Calculator logic ---------------------------------------------
    def _press(self, value):
        if value == "clear":
            self.expression = ""
            self.result.set("Ready")
            self.history_index = -1
        elif value == "delete":
            self.expression = self.expression[:-1]
        elif value == "equals":
            self._calculate()
            return
        elif value == "percent":
            self.expression += "/100"
        elif value == "negate":
            self.expression = f"-({self.expression})" if self.expression else "-"
        else:
            if self.just_calculated and value not in self.CONTINUE:
                self.expression = ""
            self.expression += "**" if value == "^" else value
        self.just_calculated = False
        self._refresh_display()

    def _calculate(self):
        if not self.expression:
            return
        try:
            value = evaluate_expression(self.expression, self.angle_mode.get())
        except CalculatorError as error:
            self.result.set(str(error))
            return
        except (ArithmeticError, ValueError, TypeError):
            self.result.set("Math error")
            return
        formatted = self._format_number(value)
        self.history_items.insert(0, (self.expression, formatted))
        self.history.insert(0, f"{self._shown_expression()} = {formatted}")
        if len(self.history_items) > 30:
            self.history_items.pop()
            self.history.delete(30, tk.END)
        self.expression = formatted
        self.result.set(formatted)
        self.just_calculated = True
        self.history_index = -1
        self._refresh_display()

    def insert_value(self, value):
        """Called by the fitness/finance dialogs to drop a result into the calculator."""
        text = self._format_number(value)
        if self.just_calculated or not self.expression or self.expression[-1] not in "+-*/%(":
            self.expression = text
        else:
            self.expression += text
        self.just_calculated = False
        self.result.set("Inserted")
        self._refresh_display()

    def _format_number(self, value):
        if isinstance(value, int):
            return str(value)
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.12g}"

    def _shown_expression(self):
        text = self.expression.replace("**", "^").replace("//", "\0")
        text = text.replace("*", "×").replace("/", "÷").replace("\0", "//")
        return text.replace("%", " mod ").replace("pi", "π")

    def _refresh_display(self):
        self.display.set(self._shown_expression() or "0")

    def _toggle_angle_mode(self):
        self.angle_mode.set("RAD" if self.angle_mode.get() == "DEG" else "DEG")

    # ---- History -------------------------------------------------------
    def _clear_history(self):
        self.history.delete(0, tk.END)
        self.history_items.clear()
        self.history_index = -1
        self.root.focus_set()

    def _load_history(self, index):
        self.expression = self.history_items[index][0]
        self.just_calculated = False
        self.result.set("Recalled from history")
        self._refresh_display()
        self.history.selection_clear(0, tk.END)
        self.history.selection_set(index)
        self.history.see(index)

    def _history_step(self, step):
        if not self.history_items:
            return
        index = min(max(self.history_index + step, -1), len(self.history_items) - 1)
        self.history_index = index
        if index == -1:
            self.history.selection_clear(0, tk.END)
            self._press("clear")
        else:
            self._load_history(index)

    def _recall_history_click(self, _event):
        selection = self.history.curselection()
        if selection:
            self.history_index = selection[0]
            self._load_history(selection[0])
        self.root.focus_set()

    # ---- Tools ---------------------------------------------------------
    def open_tool(self, tool):
        if self.tool_window is not None and self.tool_window.winfo_exists():
            self.tool_window.close()
        self.tool_window = ToolDialog(self, tool)


if __name__ == "__main__":
    app_root = tk.Tk()
    ScientificCalculator(app_root)
    app_root.mainloop()
