import requests
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from bs4 import BeautifulSoup


class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect("stocks.db")
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                current_price REAL,
                entry_price REAL,
                quantity INTEGER,
                stop_loss REAL,
                target REAL,
                trade_type TEXT
            )
        """)
        self.conn.commit()

    def add_stock(self, symbol, current_price, entry_price, quantity, stop_loss, target, trade_type):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO stocks 
            (symbol, current_price, entry_price, quantity, stop_loss, target, trade_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol.upper(), current_price, entry_price, quantity, stop_loss, target, trade_type))
        self.conn.commit()

    def update_stock(self, stock_id, symbol, current_price, entry_price, quantity, stop_loss, target, trade_type):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE stocks 
            SET symbol=?, current_price=?, entry_price=?, quantity=?, stop_loss=?, target=?, trade_type=?
            WHERE id=?
        """, (symbol.upper(), current_price, entry_price, quantity, stop_loss, target, trade_type, stock_id))
        self.conn.commit()

    def get_stocks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM stocks")
        return cursor.fetchall()

    def delete_stock(self, stock_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM stocks WHERE id=?", (stock_id,))
        self.conn.commit()


class StockTracker:
    def __init__(self, root):
        self.root = root
        self.db = DatabaseHandler()
        self.current_edit_id = None
        self.current_price = 0.0
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        self.root.title("Stock Portfolio Manager")
        self.root.geometry("1100x700")
        self.root.configure(bg="#F5F5F5")

        style = ttk.Style()
        style.configure("TFrame", background="#F5F5F5")
        style.configure("TButton", font=("Arial", 10), padding=6)
        style.configure("Header.TLabel", font=("Arial", 14, "bold"), background="#3F51B5", foreground="white")

        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(header_frame, text="Stock Portfolio Manager", style="Header.TLabel").pack(pady=10, fill=tk.X)

        input_frame = ttk.Frame(self.root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        symbol_frame = ttk.Frame(input_frame)
        symbol_frame.pack(fill=tk.X, pady=5)
        ttk.Label(symbol_frame, text="Stock Symbol:").pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(symbol_frame, width=20)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(symbol_frame, text="Fetch Price", command=self.fetch_current_price).pack(side=tk.LEFT, padx=5)
        self.current_price_label = ttk.Label(symbol_frame, text="Current: ₹0.00")
        self.current_price_label.pack(side=tk.RIGHT, padx=10)

        trade_type_frame = ttk.Frame(input_frame)
        trade_type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(trade_type_frame, text="Trade Type:").pack(side=tk.LEFT)
        self.trade_type = tk.StringVar()
        self.trade_selector = ttk.Combobox(trade_type_frame, textvariable=self.trade_type,
                                           values=["Bullish", "Bearish"], state="readonly", width=12)
        self.trade_selector.pack(side=tk.LEFT)
        self.trade_selector.bind("<<ComboboxSelected>>", self.update_slider_ranges)

        entry_price_frame = ttk.Frame(input_frame)
        entry_price_frame.pack(fill=tk.X, pady=5)
        self.entry_price_var = tk.DoubleVar()
        ttk.Label(entry_price_frame, text="Entry Price:").pack(side=tk.LEFT)
        self.entry_price_entry = ttk.Entry(entry_price_frame, textvariable=self.entry_price_var, width=10)
        self.entry_price_entry.pack(side=tk.LEFT, padx=5)
        self.entry_price_slider = ttk.Scale(
            entry_price_frame,
            from_=0,
            to=100,
            variable=self.entry_price_var,
            orient=tk.HORIZONTAL
        )
        self.entry_price_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        quantity_frame = ttk.Frame(input_frame)
        quantity_frame.pack(fill=tk.X, pady=5)
        self.quantity_var = tk.IntVar()
        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT)
        self.quantity_entry = ttk.Entry(quantity_frame, textvariable=self.quantity_var, width=10)
        self.quantity_entry.pack(side=tk.LEFT, padx=5)
        self.quantity_slider = ttk.Scale(
            quantity_frame,
            from_=0,
            to=1000,
            variable=self.quantity_var,
            orient=tk.HORIZONTAL
        )
        self.quantity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        stop_loss_frame = ttk.Frame(input_frame)
        stop_loss_frame.pack(fill=tk.X, pady=5)
        self.stop_loss_var = tk.DoubleVar()
        ttk.Label(stop_loss_frame, text="Stop Loss:").pack(side=tk.LEFT)
        self.stop_loss_entry = ttk.Entry(stop_loss_frame, textvariable=self.stop_loss_var, width=10)
        self.stop_loss_entry.pack(side=tk.LEFT, padx=5)
        self.stop_loss_slider = ttk.Scale(
            stop_loss_frame,
            from_=0,
            to=100,
            variable=self.stop_loss_var,
            orient=tk.HORIZONTAL
        )
        self.stop_loss_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        target_frame = ttk.Frame(input_frame)
        target_frame.pack(fill=tk.X, pady=5)
        self.target_var = tk.DoubleVar()
        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_var, width=10)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        self.target_slider = ttk.Scale(
            target_frame,
            from_=0,
            to=100,
            variable=self.target_var,
            orient=tk.HORIZONTAL
        )
        self.target_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Add Stock", command=self.add_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Stock", command=self.update_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        list_frame = ttk.Frame(self.root)
        list_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        columns = [
            ("id", "ID", 50),
            ("symbol", "Symbol", 100),
            ("current_price", "Current", 100),
            ("entry_price", "Entry", 100),
            ("quantity", "Qty", 80),
            ("investment", "Invested", 120),
            ("stop_loss", "Stop Loss", 100),
            ("target", "Target", 100),
            ("trade_type", "Type", 80),
            ("profit_pct", "P/L %", 100)
        ]

        self.tree = ttk.Treeview(list_frame, columns=[col[0] for col in columns], show="headings", selectmode="browse")

        for col in columns:
            self.tree.heading(col[0], text=col[1])
            self.tree.column(col[0], width=col[2], anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.tree.tag_configure('bullish', background='#e6f3ff')
        self.tree.tag_configure('bearish', background='#ffe6e6')

    def update_slider_ranges(self, event=None):
        if self.current_price > 0:
            trade_type = self.trade_type.get()

            if trade_type == "Bullish":
                self.entry_price_slider.config(from_=self.current_price * 0.9, to=self.current_price * 1.1)
                self.stop_loss_slider.config(from_=self.current_price * 0.8, to=self.current_price * 0.98)
                self.target_slider.config(from_=self.current_price * 1.02, to=self.current_price * 1.2)
            elif trade_type == "Bearish":
                self.entry_price_slider.config(from_=self.current_price * 0.9, to=self.current_price * 1.1)
                self.stop_loss_slider.config(from_=self.current_price * 1.02, to=self.current_price * 1.2)
                self.target_slider.config(from_=self.current_price * 0.8, to=self.current_price * 0.98)

            self.entry_price_var.set(round(self.current_price, 2))
            self.set_defaults_based_on_type()

    def set_defaults_based_on_type(self):
        trade_type = self.trade_type.get()
        entry_price = self.entry_price_var.get()

        if trade_type == "Bullish":
            self.stop_loss_var.set(round(entry_price * 0.95, 2))
            self.target_var.set(round(entry_price * 1.05, 2))
        elif trade_type == "Bearish":
            self.stop_loss_var.set(round(entry_price * 1.05, 2))
            self.target_var.set(round(entry_price * 0.95, 2))

    def fetch_current_price(self):
        symbol = self.symbol_entry.get().strip()
        if not symbol:
            messagebox.showwarning("Warning", "Please enter a stock symbol")
            return

        try:
            import certifi  # Add this import at the top of your file
            self.current_price = self.get_stock_price(symbol)
            if self.current_price > 0:
                self.current_price_label.config(text=f"Current: ₹{self.current_price:.2f}")
                self.update_slider_ranges()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch price: {str(e)}")

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for stock in self.db.get_stocks():
            profit_pct = self.calculate_profit_percentage(stock[2], stock[3])
            investment = stock[3] * stock[4]
            tags = ('bullish' if stock[7] == "Bullish" else 'bearish',)
            self.tree.insert("", tk.END, values=(
                stock[0],  # ID
                stock[1],  # Symbol
                f"₹{stock[2]:.2f}",  # Current
                f"₹{stock[3]:.2f}",  # Entry
                stock[4],  # Qty
                f"₹{investment:.2f}",  # Invested
                f"₹{stock[5]:.2f}",  # SL
                f"₹{stock[6]:.2f}",  # Target
                stock[7],  # Type
                f"{profit_pct:.2f}%"  # P/L %
            ), tags=tags)

    def calculate_profit_percentage(self, current_price, entry_price):
        if entry_price == 0:
            return 0.0
        return ((current_price - entry_price) / entry_price) * 100

    def get_stock_price(self, symbol):
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        try:
            import certifi  # Add this import at the top
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=certifi.where())
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            price_element = soup.select_one("div.YMlKec.fxKbKc")
            if price_element:
                return float(price_element.text.strip().replace("₹", "").replace(",", ""))
            return 0
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch price: {str(e)}")
            return 0

    def add_stock(self):
        symbol = self.symbol_entry.get().strip()
        entry_price = round(self.entry_price_var.get(), 2)
        quantity = self.quantity_var.get()
        stop_loss = round(self.stop_loss_var.get(), 2)
        target = round(self.target_var.get(), 2)
        trade_type = self.trade_type.get()

        if not symbol:
            messagebox.showwarning("Warning", "Please enter a stock symbol")
            return

        if self.current_price <= 0:
            messagebox.showwarning("Warning", "Please fetch current price first")
            return

        if not trade_type:
            messagebox.showwarning("Warning", "Please select a trade type")
            return

        try:
            self.db.add_stock(symbol, self.current_price, entry_price, quantity,
                              stop_loss, target, trade_type)
            self.refresh_list()
            self.clear_fields()
            messagebox.showinfo("Success", "Stock added successfully")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Stock already exists in portfolio")

    def update_stock(self):
        if not self.current_edit_id:
            messagebox.showwarning("Warning", "No stock selected for editing")
            return

        symbol = self.symbol_entry.get().strip()
        entry_price = round(self.entry_price_var.get(), 2)
        quantity = self.quantity_var.get()
        stop_loss = round(self.stop_loss_var.get(), 2)
        target = round(self.target_var.get(), 2)
        trade_type = self.trade_type.get()

        if not symbol:
            messagebox.showwarning("Warning", "Please enter a stock symbol")
            return

        if self.current_price <= 0:
            messagebox.showwarning("Warning", "Please fetch current price first")
            return

        self.db.update_stock(
            self.current_edit_id,
            symbol,
            self.current_price,
            entry_price,
            quantity,
            stop_loss,
            target,
            trade_type
        )
        self.refresh_list()
        self.clear_fields()
        messagebox.showinfo("Success", "Stock updated successfully")
        self.current_edit_id = None

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a stock to delete")
            return
        try:
            stock_id = int(self.tree.item(selected[0], "values")[0])
            if messagebox.askyesno("Confirm", "Delete this stock from portfolio?"):
                self.db.delete_stock(stock_id)
                self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete stock: {str(e)}")

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a stock to edit")
            return
        try:
            stock = self.tree.item(selected[0], "values")
            self.current_edit_id = int(stock[0])

            self.current_price = self.get_stock_price(stock[1])
            if self.current_price <= 0:
                return

            self.current_price_label.config(text=f"Current: ₹{self.current_price:.2f}")

            self.trade_type.set(stock[8])
            self.update_slider_ranges()

            self.symbol_entry.delete(0, tk.END)
            self.symbol_entry.insert(0, stock[1])
            self.entry_price_var.set(float(stock[3].replace("₹", "")))
            self.quantity_var.set(int(stock[4]))
            self.stop_loss_var.set(float(stock[6].replace("₹", "")))
            self.target_var.set(float(stock[7].replace("₹", "")))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit stock: {str(e)}")

    def clear_fields(self):
        self.symbol_entry.delete(0, tk.END)
        self.current_price_label.config(text="Current: ₹0.00")
        self.entry_price_var.set(0)
        self.quantity_var.set(0)
        self.stop_loss_var.set(0)
        self.target_var.set(0)
        self.trade_type.set('')
        self.current_price = 0.0
        self.current_edit_id = None

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    app = StockTracker(root)
    root.mainloop()