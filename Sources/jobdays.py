# -*- coding: utf-8 -*-
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import bd_unit
from univunit import Table, Univunit
from ttkbootstrap import DateEntry, ttk

DB_MANAGER = bd_unit.DatabaseManager()
ICON_PATH = bd_unit.ICON_PATH

class JobDaysApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.geometry("500x400")
        self.title("Добавление рабочих дней для получения FTE")
        self.hours_var = tk.IntVar()
        self.middle_days_var = tk.StringVar()
        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)
        self.result_label = None
        self.mdf = None

        self.create_widgets()

        self.table_job = Table(self)
        self.table_job.menu.add_command(label="Добавить запись", command=self.save_days)
        self.table_job.menu.add_command(label="Удалить запись", command=self.delete_selected)

        self.table_job.pack(expand=True, fill='both')
        self.read_all_data()

    def create_widgets(self):
        style = ttk.Style()
        # style.theme_use('clam')
        # style.configure("my.TButton", font=("Arial", 12), background="red")
        style.configure('My.TButton', background="#FF3399", foreground="white", font=("Arial", 20), padding=5)
        frame_item = tk.Frame(self)

        tk.Label(frame_item, text='Среднее часов', bg="#333333", fg="white", font=("Arial", 12)).grid(
            row=1,
            sticky="e")
        self.mdf = tk.Entry(frame_item, textvariable=self.middle_days_var, font=("Arial", 12), width=5)
        self.mdf.grid(row=1, column=1, pady=20, padx=10, sticky="ew")

        ttk.Button(frame_item, text='Сохранить',
                   command=self.save_middle_days,
                   style='My.TButton'
                   ).grid(row=1, column=2, pady=20, padx=10, sticky="ew")

        frame_item_period = tk.Frame(frame_item)
        tk.Label(frame_item_period, text='Период', bg="#333333", fg="white", font=("Arial", 16)).pack(side="left")
        # .grid(row=2, column=0, sticky="e")
        self.month_year = (DateEntry(master=frame_item_period, width=12, relief="solid", dateformat='%d-%m-%Y')
                           .pack(side="left", padx=10))

        tk.Label(frame_item_period, text='часы', bg="#333333", fg="white", font=("Arial", 16)).pack(side="left",
                                                                                                    padx=5)
        tk.Entry(frame_item_period, textvariable=self.hours_var, font=("Arial", 12), width=5).pack(side="left", padx=5)
        tk.Button(frame_item_period, text='Добавить',
                  command=self.save_days,
                  bg="#FF3399", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        frame_item_period.grid(row=3, columnspan=5, padx=10)

        # Место для отображения результата входа
        self.result_label = tk.Label(frame_item, bg="#333333", fg="blue", font=("Arial", 10))
        self.result_label.grid(row=4, columnspan=2, sticky="ew")

        # frame_buttons = tk.Frame(frame_item)
        #
        # frame_buttons.grid(row=5, columnspan=2, pady=10)
        frame_item.pack(side=tk.TOP, fill=tk.X)

    def add_month_name_first(self, tuples_list):
        """
            Добавление в кортеж имени месяца
        """
        updated_list = []
        for item in tuples_list:
            date_str, work_days = item
            month_name = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B')
            updated_list.append((month_name, date_str, work_days))
        return updated_list

    def read_all_data(self):

        self.mdf.config(state=tk.NORMAL)
        self.mdf.delete(0, tk.END)

        middle_days_var = DB_MANAGER.get_middle_fte()
        if middle_days_var != '0':
            self.mdf.insert(0, str(middle_days_var))

        self.table_job.configure_columns([{'name': 'Месяц', 'anchor': 'left'}, {'name': 'Период'},
                                          {'name': 'Часы', 'width': 50}])
        data = self.add_month_name_first(DB_MANAGER.read_all_table())

        self.table_job.populate_table(data)

    def delete_selected(self):
        """
        Метод для удаления выделенных записей из таблицы.
        """
        selected_items = self.table_job.tree.selection()
        selected_values = [self.table_job.tree.item(item, 'values') for item in selected_items]
        if not selected_items:
            self.result_label.config(text="Нет выбранных записей для удаления.", fg="red")
            return

        try:
            for item in selected_values:
                DB_MANAGER.delete_record(item[1])
                self.result_label.config(text=f"За период {item[1]} удалена запись")
            self.read_all_data()

        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не удалены: {e}")

        self.result_label.config(text="Выбранные записи удалены.", fg="blue")

    def save_days(self):
        try:
            days = self.hours_var.get()
            if days == 0:
                raise ValueError("Количество дней не может быть нулевым.")
            date_in = datetime.strptime(self.month_year.entry.get(), '%d-%m-%Y')
            date_in = Univunit.first_date_of_month(date_in)
            DB_MANAGER.insert_data([(self.hours_var.get(), date_in)])
            self.result_label.config(text=f"{date_in}, число:{self.hours_var.get()} добавлены")
            self.read_all_data()
        except ValueError as ve:
            messagebox.showinfo('Ошибка ввода', str(ve))
        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не сохранены: {e}")

    def save_middle_days(self):
        try:
            days = self.middle_days_var.get()
            if days == 0:
                days = 164
            DB_MANAGER.save_middle_fte(days)
            self.result_label.config(text=f"Среднее:{days} добавлено")
            self.read_all_data()
        except ValueError as ve:
            messagebox.showinfo('Ошибка ввода', str(ve))
        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не сохранены: {e}")
