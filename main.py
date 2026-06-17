from __future__ import annotations

import ast
import json
import math
import operator
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


HISTORY_PATH = Path.home() / ".scientific_calculator_history.json"


class CalculationError(Exception):
    pass


class ExpressionCalculator:
    def __init__(self):
        self.angle_mode = "DEG"
        self.memory = 0.0
        self.answer = 0.0

        self.binary_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.FloorDiv: operator.floordiv,
        }

        self.unary_ops = {
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }

    def to_radians(self, value):
        if self.angle_mode == "DEG":
            return math.radians(value)
        return value

    def from_radians(self, value):
        if self.angle_mode == "DEG":
            return math.degrees(value)
        return value

    def factorial(self, value):
        if value < 0 or not float(value).is_integer():
            raise CalculationError("Factorial needs a non-negative integer.")
        if value > 5000:
            raise CalculationError("That number is too large for factorial.")
        return math.factorial(int(value))

    def cube_root(self, value):
        return math.copysign(abs(value) ** (1 / 3), value)

    def functions(self):
        return {
            "sin": lambda x: math.sin(self.to_radians(x)),
            "cos": lambda x: math.cos(self.to_radians(x)),
            "tan": lambda x: math.tan(self.to_radians(x)),
            "asin": lambda x: self.from_radians(math.asin(x)),
            "acos": lambda x: self.from_radians(math.acos(x)),
            "atan": lambda x: self.from_radians(math.atan(x)),
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "sqrt": math.sqrt,
            "cbrt": self.cube_root,
            "ln": math.log,
            "log": math.log10,
            "log2": math.log2,
            "exp": math.exp,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
            "round": round,
            "factorial": self.factorial,
            "percent": lambda x: x / 100,
            "pow": math.pow,
        }

    def constants(self):
        return {
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "ans": self.answer,
            "mem": self.memory,
        }

    def clean_expression(self, expression):
        replacements = {
            "×": "*",
            "÷": "/",
            "−": "-",
            "^": "**",
            "π": "pi",
            "√": "sqrt",
        }

        expression = expression.strip()

        for old, new in replacements.items():
            expression = expression.replace(old, new)

        return expression

    def calculate(self, expression):
        expression = self.clean_expression(expression)

        if not expression:
            raise CalculationError("Enter an expression.")

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as error:
            raise CalculationError("The expression is not valid.") from error

        result = self.read_node(tree.body)

        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise CalculationError("The result is not supported.")

        if isinstance(result, float) and not math.isfinite(result):
            raise CalculationError("The result is not finite.")

        return result

    def read_node(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise CalculationError("Only numbers are allowed.")
            return node.value

        if isinstance(node, ast.BinOp):
            operation = self.binary_ops.get(type(node.op))

            if operation is None:
                raise CalculationError("This operator is not supported.")

            left = self.read_node(node.left)
            right = self.read_node(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10000:
                raise CalculationError("The exponent is too large.")

            try:
                return operation(left, right)
            except ZeroDivisionError as error:
                raise CalculationError("You cannot divide by zero.") from error
            except (ValueError, OverflowError) as error:
                raise CalculationError(str(error)) from error

        if isinstance(node, ast.UnaryOp):
            operation = self.unary_ops.get(type(node.op))

            if operation is None:
                raise CalculationError("This unary operator is not supported.")

            return operation(self.read_node(node.operand))

        if isinstance(node, ast.Name):
            values = self.constants()

            if node.id not in values:
                raise CalculationError(f"Unknown value: {node.id}")

            return values[node.id]

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise CalculationError("That function call is not allowed.")

            if node.keywords:
                raise CalculationError("Keyword arguments are not supported.")

            available = self.functions()
            name = node.func.id

            if name not in available:
                raise CalculationError(f"Unknown function: {name}")

            arguments = [self.read_node(item) for item in node.args]

            try:
                return available[name](*arguments)
            except TypeError as error:
                raise CalculationError(f"Wrong arguments for {name}().") from error
            except (ValueError, OverflowError, ZeroDivisionError) as error:
                raise CalculationError(str(error)) from error

        raise CalculationError("This expression is not supported.")


class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Scientific Calculator")
        self.geometry("980x650")
        self.minsize(860, 580)

        self.engine = ExpressionCalculator()
        self.history = []

        self.expression = tk.StringVar()
        self.result = tk.StringVar(value="0")
        self.status = tk.StringVar(value="Ready")
        self.angle_mode = tk.StringVar(value="DEG")

        self.setup_style()
        self.build_window()
        self.bind_keys()
        self.load_history()

        self.entry.focus_set()

    def setup_style(self):
        style = ttk.Style(self)

        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Display.TEntry", font=("Segoe UI", 20))
        style.configure("Result.TLabel", font=("Segoe UI Semibold", 26))
        style.configure("Key.TButton", font=("Segoe UI", 12), padding=8)
        style.configure("Equal.TButton", font=("Segoe UI Semibold", 12), padding=8)
        style.configure("Heading.TLabel", font=("Segoe UI Semibold", 18))

    def build_window(self):
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self, padding=14)
        right = ttk.Frame(self, padding=(0, 14, 14, 14))

        left.grid(row=0, column=0, sticky="nsew")
        right.grid(row=0, column=1, sticky="nsew")

        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.build_display(left)
        self.build_toolbar(left)
        self.build_keys(left)
        self.build_history_panel(right)

        status_bar = ttk.Label(self, textvariable=self.status, anchor="w", padding=(8, 4))
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def build_display(self, parent):
        box = ttk.LabelFrame(parent, text="Expression", padding=12)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(
            box,
            textvariable=self.expression,
            style="Display.TEntry",
            justify="right",
        )
        self.entry.grid(row=0, column=0, sticky="ew", ipady=8)

        result_label = ttk.Label(
            box,
            textvariable=self.result,
            style="Result.TLabel",
            anchor="e",
        )
        result_label.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def build_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(toolbar, text="Angle:").pack(side="left")

        angle_box = ttk.Combobox(
            toolbar,
            width=7,
            state="readonly",
            values=("DEG", "RAD"),
            textvariable=self.angle_mode,
        )
        angle_box.pack(side="left", padx=(6, 14))
        angle_box.bind("<<ComboboxSelected>>", self.change_angle)

        ttk.Button(toolbar, text="Copy Result", command=self.copy_result).pack(
            side="left", padx=3
        )
        ttk.Button(toolbar, text="Clear History", command=self.clear_history).pack(
            side="left", padx=3
        )
        ttk.Button(toolbar, text="Help", command=self.show_help).pack(
            side="right", padx=3
        )

    def build_keys(self, parent):
        keypad = ttk.Frame(parent)
        keypad.grid(row=2, column=0, sticky="nsew")

        for column in range(7):
            keypad.columnconfigure(column, weight=1, uniform="column")

        for row in range(8):
            keypad.rowconfigure(row, weight=1, uniform="row")

        keys = [
            ("MC", self.memory_clear),
            ("MR", self.memory_recall),
            ("M+", self.memory_add),
            ("M-", self.memory_subtract),
            ("⌫", self.backspace),
            ("CE", self.clear_entry),
            ("C", self.reset),
            ("sin", lambda: self.add_function("sin")),
            ("cos", lambda: self.add_function("cos")),
            ("tan", lambda: self.add_function("tan")),
            ("asin", lambda: self.add_function("asin")),
            ("acos", lambda: self.add_function("acos")),
            ("atan", lambda: self.add_function("atan")),
            ("(", lambda: self.add_text("(")),
            ("sinh", lambda: self.add_function("sinh")),
            ("cosh", lambda: self.add_function("cosh")),
            ("tanh", lambda: self.add_function("tanh")),
            ("ln", lambda: self.add_function("ln")),
            ("log", lambda: self.add_function("log")),
            ("log₂", lambda: self.add_function("log2")),
            (")", lambda: self.add_text(")")),
            ("√", lambda: self.add_function("sqrt")),
            ("∛", lambda: self.add_function("cbrt")),
            ("x²", lambda: self.add_text("**2")),
            ("xʸ", lambda: self.add_text("**")),
            ("1/x", self.add_reciprocal),
            ("n!", lambda: self.add_function("factorial")),
            ("%", lambda: self.add_function("percent")),
            ("7", lambda: self.add_text("7")),
            ("8", lambda: self.add_text("8")),
            ("9", lambda: self.add_text("9")),
            ("÷", lambda: self.add_text("/")),
            ("π", lambda: self.add_text("pi")),
            ("e", lambda: self.add_text("e")),
            ("Ans", lambda: self.add_text("ans")),
            ("4", lambda: self.add_text("4")),
            ("5", lambda: self.add_text("5")),
            ("6", lambda: self.add_text("6")),
            ("×", lambda: self.add_text("*")),
            ("abs", lambda: self.add_function("abs")),
            ("floor", lambda: self.add_function("floor")),
            ("ceil", lambda: self.add_function("ceil")),
            ("1", lambda: self.add_text("1")),
            ("2", lambda: self.add_text("2")),
            ("3", lambda: self.add_text("3")),
            ("−", lambda: self.add_text("-")),
            ("exp", lambda: self.add_function("exp")),
            ("mod", lambda: self.add_text("%")),
            ("±", self.change_sign),
            ("0", lambda: self.add_text("0")),
            (".", lambda: self.add_text(".")),
            (",", lambda: self.add_text(",")),
            ("+", lambda: self.add_text("+")),
            ("τ", lambda: self.add_text("tau")),
            ("Mem", lambda: self.add_text("mem")),
            ("=", self.run_calculation),
        ]

        for index, item in enumerate(keys):
            text, action = item
            row, column = divmod(index, 7)
            style = "Equal.TButton" if text == "=" else "Key.TButton"

            button = ttk.Button(keypad, text=text, command=action, style=style)
            button.grid(row=row, column=column, sticky="nsew", padx=3, pady=3)

    def build_history_panel(self, parent):
        ttk.Label(parent, text="History", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        box = ttk.Frame(parent)
        box.grid(row=1, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        self.history_list = tk.Listbox(
            box,
            font=("Consolas", 11),
            activestyle="dotbox",
            exportselection=False,
        )
        self.history_list.grid(row=0, column=0, sticky="nsew")
        self.history_list.bind("<Double-Button-1>", self.reuse_history)
        self.history_list.bind("<Return>", self.reuse_history)

        scroll = ttk.Scrollbar(box, orient="vertical", command=self.history_list.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.history_list.configure(yscrollcommand=scroll.set)

        ttk.Label(
            parent,
            text="Double-click a calculation to use it again.",
            wraplength=250,
        ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def bind_keys(self):
        self.bind("<Return>", lambda event: self.run_calculation())
        self.bind("<KP_Enter>", lambda event: self.run_calculation())
        self.bind("<Escape>", lambda event: self.reset())
        self.bind("<Control-l>", lambda event: self.reset())
        self.bind("<Control-c>", lambda event: self.copy_result())
        self.entry.bind("<KeyRelease>", self.preview)

    def selected_text(self):
        try:
            return self.entry.selection_get()
        except tk.TclError:
            return ""

    def add_text(self, text):
        self.entry.insert(tk.INSERT, text)
        self.entry.focus_set()
        self.preview()

    def add_function(self, name):
        selected = self.selected_text()

        if selected:
            self.add_text(f"{name}({selected})")
        else:
            self.add_text(f"{name}(")

    def add_reciprocal(self):
        selected = self.selected_text()

        if selected:
            self.add_text(f"1/({selected})")
        else:
            self.add_text("1/(")

    def backspace(self):
        try:
            start = self.entry.index(tk.SEL_FIRST)
            end = self.entry.index(tk.SEL_LAST)
            self.entry.delete(start, end)
        except tk.TclError:
            cursor = self.entry.index(tk.INSERT)

            if cursor > 0:
                self.entry.delete(cursor - 1, cursor)

        self.preview()

    def clear_entry(self):
        self.expression.set("")
        self.result.set("0")
        self.status.set("Entry cleared")
        self.entry.focus_set()

    def reset(self):
        self.clear_entry()
        self.engine.answer = 0.0
        self.status.set("Calculator reset")

    def change_sign(self):
        text = self.expression.get().strip()

        if not text:
            self.expression.set("-")
        elif text.startswith("-(") and text.endswith(")"):
            self.expression.set(text[2:-1])
        else:
            self.expression.set(f"-({text})")

        self.preview()

    def run_calculation(self):
        text = self.expression.get()

        try:
            value = self.engine.calculate(text)
            formatted = self.format_number(value)

            self.engine.answer = float(value)
            self.result.set(formatted)
            self.status.set(f"Calculated in {self.engine.angle_mode} mode")
            self.add_history(text, formatted)
        except CalculationError as error:
            self.result.set("Error")
            self.status.set(str(error))

        self.entry.focus_set()

    def preview(self, event=None):
        text = self.expression.get().strip()

        if not text:
            self.result.set("0")
            return

        try:
            value = self.engine.calculate(text)
            self.result.set(self.format_number(value))
            self.status.set("Preview")
        except CalculationError:
            pass

    def format_number(self, value):
        if isinstance(value, int):
            return str(value)

        if math.isclose(value, round(value), abs_tol=1e-12):
            return str(round(value))

        if abs(value) >= 1e12 or 0 < abs(value) < 1e-9:
            return f"{value:.12e}"

        return f"{value:.12g}"

    def change_angle(self, event=None):
        self.engine.angle_mode = self.angle_mode.get()
        self.status.set(f"Angle mode: {self.engine.angle_mode}")
        self.preview()

    def current_value(self):
        try:
            return float(self.engine.calculate(self.expression.get()))
        except CalculationError as error:
            self.status.set(str(error))
            return None

    def memory_clear(self):
        self.engine.memory = 0.0
        self.status.set("Memory cleared")

    def memory_recall(self):
        self.add_text(self.format_number(self.engine.memory))
        self.status.set("Memory recalled")

    def memory_add(self):
        value = self.current_value()

        if value is not None:
            self.engine.memory += value
            self.status.set(f"Memory = {self.format_number(self.engine.memory)}")

    def memory_subtract(self):
        value = self.current_value()

        if value is not None:
            self.engine.memory -= value
            self.status.set(f"Memory = {self.format_number(self.engine.memory)}")

    def add_history(self, expression, result):
        expression = expression.strip()

        if not expression:
            return

        self.history.append({"expression": expression, "result": result})
        self.history = self.history[-100:]

        self.refresh_history()
        self.save_history()

    def refresh_history(self):
        self.history_list.delete(0, tk.END)

        for item in reversed(self.history):
            text = f'{item["expression"]} = {item["result"]}'
            self.history_list.insert(tk.END, text)

    def reuse_history(self, event=None):
        selected = self.history_list.curselection()

        if not selected:
            return

        index = len(self.history) - 1 - selected[0]
        self.expression.set(self.history[index]["expression"])
        self.entry.icursor(tk.END)
        self.preview()
        self.entry.focus_set()

    def clear_history(self):
        if not self.history:
            return

        confirmed = messagebox.askyesno(
            "Clear history",
            "Delete all saved calculations?",
        )

        if confirmed:
            self.history.clear()
            self.refresh_history()
            self.save_history()
            self.status.set("History cleared")

    def load_history(self):
        try:
            if HISTORY_PATH.exists():
                data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))

                if isinstance(data, list):
                    self.history = [
                        item
                        for item in data
                        if isinstance(item, dict)
                        and "expression" in item
                        and "result" in item
                    ][-100:]
        except (OSError, json.JSONDecodeError):
            self.history = []

        self.refresh_history()

    def save_history(self):
        try:
            HISTORY_PATH.write_text(
                json.dumps(self.history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            self.status.set("History could not be saved")

    def copy_result(self):
        text = self.result.get()

        if text and text != "Error":
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.set("Result copied")

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "Examples:\n"
            "sin(30) + cos(60)\n"
            "sqrt(144) + 2**8\n"
            "log(1000)\n"
            "factorial(6)\n"
            "percent(15) * 200\n"
            "pow(2, 10)\n\n"
            "Constants: pi, e, tau, ans, mem\n"
            "Enter: calculate\n"
            "Escape: clear\n"
            "Ctrl+C: copy result",
        )


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
