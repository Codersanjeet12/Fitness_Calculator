# Fitness_Calculator
Awesome Scientific ,Fitness, Finincial &amp; Age Calcultor 
# Scientific Calculator with Fitness & Finance Tools

A desktop calculator built with Python and Tkinter. It combines a scientific calculator with built-in **fitness**, **finance** and **age** tools, all in one compact, dark-themed window that can be driven entirely from the keyboard.

> Built as part of my Data Science & AI learning journey. No external libraries needed, just Python's standard library.

---

## Features

### Scientific calculator
- Basic operations: `+`, `-`, `×`, `÷`, `%`, `mod`, floor division (`//`), power (`^`)
- Functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `log`, `abs`, `exp`, `fact` (factorial)
- Constants: `π` and `e`
- **DEG / RAD** toggle for trigonometric functions
- Safe expression parsing using Python's `ast` module (no `eval()`), with guards against huge exponents and factorials
- Calculation **history** (last 30 results) with click or Up/Down arrow recall
- Copy / paste support (`Ctrl+C`, `Ctrl+V`)
- Show or hide the Scientific, Tools and History sections like the "more" panel on a phone calculator

### Fitness tools
| Tool | What it gives you |
|------|-------------------|
| **BMI** | BMI value, category and healthy weight range |
| **BMR & Daily Calories** | BMR (Mifflin-St Jeor), maintenance calories, weight loss and weight gain targets |
| **Daily Water Intake** | Recommended litres per day based on weight and exercise time |
| **Ideal Weight** | Ideal weight and ±10% range (Devine formula) |
| **Heart Rate Zones** | Max heart rate and Warm-up, Fat burn, Cardio and Peak zones |

### Finance tools (Indian rupee format, e.g. `₹12,34,567.00`)
| Tool | What it gives you |
|------|-------------------|
| **EMI** | Monthly EMI, total payment and total interest |
| **Simple Interest** | Interest and total amount |
| **Compound Interest** | Interest and total amount with custom compounding frequency |
| **GST** | Add or remove GST, with CGST and SGST split |
| **SIP** | Maturity value, amount invested and gain |

### Other
- **Age Calculator**: exact age in years, months and days, total months/weeks/days, birth weekday and days until next birthday (handles 29 Feb births)

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` or `=` | Calculate |
| `Esc` or `Delete` | Clear |
| `Backspace` | Delete last character |
| `Tab` | Toggle DEG / RAD |
| `↑` / `↓` | Recall previous / next history item |
| `Ctrl + 1` to `Ctrl + 5` | Fitness tools (BMI, BMR, Water, Ideal Weight, Heart Rate) |
| `Ctrl + 6` to `Ctrl + 9`, `Ctrl + 0` | Finance tools (EMI, Simple Interest, Compound Interest, GST, SIP) |
| `Ctrl + A` | Age Calculator |
| `Ctrl + S` / `Ctrl + T` / `Ctrl + H` | Show or hide Scientific / Tools / History |
| `Ctrl + C` / `Ctrl + V` | Copy result / paste expression |

Inside a tool dialog: `Enter` = calculate, `Ctrl + Enter` = insert the result into the calculator, `Esc` = close.

---

## Getting started

### Requirements
- Python 3.8 or higher
- Tkinter (comes bundled with most Python installations)

### Run

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
python Proj2_calculator.py
```

---

## Example expressions

```
sin(30)            -> 0.5       (in DEG mode)
fact(5) + 2^3      -> 128
log(1000)          -> 3
(2+3)*pi           -> 15.70796326795
```

---

## Project structure

```
.
├── Proj2_calculator.py   # Complete application (evaluator, tools, GUI)
└── README.md
```

Main parts of the code:
- `evaluate_expression()` – safe AST-based expression evaluator
- `calc_*` functions – fitness, finance and age calculations
- `ToolDialog` – keyboard-driven input window for each tool
- `ScientificCalculator` – main window, keypad, history and key bindings

---

## Possible improvements

- Add input limits and a safety cap in the water intake formula
- Add more unit converters (length, weight, temperature)
- Save history between sessions
- Light theme option

---

## Author

**Sanjeet Kumar**
Data Science & AI learner | Skills: Python, SQL, Excel, Google Sheets

Feel free to open an issue or suggest improvements.

---

## License

This project is open source and available under the [MIT License](LICENSE).
