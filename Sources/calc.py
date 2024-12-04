import tkinter as tk
import univunit
import bd_unit
DB_MANAGER = bd_unit.DatabaseManager()

class CalcApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.geometry("400x200")
        self.title("Калькулятор")
        self.hours_var = tk.IntVar()
        self.var_fte = tk.StringVar()
        self.fte_on_month = tk.IntVar()
        self.Itog = None
        self.Hours = None
        self.Fte_month = None
        self.create_widgets()

    def create_widgets(self):
        frame_item = tk.Frame(self)

        tk.Label(frame_item, text='Часы', bg="#333333", fg="white", font=("Arial", 12)).grid(row=1,
                                                                                             sticky="e")
        self.Hours = tk.Entry(frame_item, textvariable=self.hours_var)
        self.Hours.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

        tk.Label(frame_item, text='FTE в месяц', bg="#333333", fg="white", font=("Arial", 12)).grid(row=2, sticky="e")

        self.Fte_month = tk.Entry(frame_item, textvariable=self.fte_on_month)
        self.Fte_month.grid(row=2, column=1, pady=5, padx=10, sticky="ew")
        fte = DB_MANAGER.get_middle_fte()
        self.Fte_month.config(state=tk.NORMAL)
        self.Fte_month.delete(0, tk.END)
        self.Fte_month.insert(0, fte)

        tk.Button(frame_item, text='Посчитать FTE',
                  command=self.get_fte,
                  bg="#FF3399", fg="white", font=("Arial", 12)).grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        tk.Button(frame_item, text='Посчитать часы',
                  command=self.get_hours,
                  bg="#FF3399", fg="white", font=("Arial", 12)).grid(row=3, column=1, pady=10, padx=10, sticky="ew")

        tk.Label(frame_item, text='FTE', bg="#333333", fg="white", font=("Arial", 12)).grid(row=4, sticky="e")
        self.Itog = tk.Entry(frame_item, textvariable=self.var_fte)
        self.Itog.grid(row=4, column=1, pady=5, padx=10, sticky="ew")

        self.Itog.config(state=tk.NORMAL)
        self.Itog.delete(0, tk.END)
        self.Itog.insert(0, '0')

        frame_item.pack(fill=tk.X, padx=50, pady=15)

    def get_hours(self):
        hours = univunit.calc_hours(fte_on_month=self.fte_on_month.get(), fte=self.var_fte.get())
        self.Hours.config(state=tk.NORMAL)
        self.Hours.delete(0, tk.END)
        self.Hours.insert(0, hours)

    def get_fte(self):
        itogo = univunit.calc_fte(fte_on_month=self.fte_on_month.get(), hours=self.hours_var.get())
        self.Itog.config(state=tk.NORMAL)
        self.Itog.delete(0, tk.END)
        self.Itog.insert(0, itogo)
