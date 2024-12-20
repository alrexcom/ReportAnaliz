# -*- coding: utf-8 -*-
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from ttkbootstrap import DateEntry


from univunit import Table, Univunit

# from reports import get_data_lukoil
import bd_unit
DB_MANAGER = bd_unit.DatabaseManager()
ICON_PATH = bd_unit.ICON_PATH

class LukoilQueries(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.geometry("800x600")
        self.title("Добавление рабочих дней для получения FTE")
        self.hours_var = tk.IntVar()
        self.num_query = tk.StringVar()
        self.num_task = tk.StringVar()
        self.description = None
        self.result_label = None
        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)
        self.create_widgets()

        self.table_fte = Table(self, height=50)
        self.table_fte.pack(expand=True, fill='both')

        self.read_all_data()

    def create_widgets(self):
        frame_item = tk.Frame(self)

        tk.Label(frame_item, text='Заявка', bg="#333333", fg="white", font=("Arial", 16)).grid(row=1,

                                                                                               sticky="e")
        txtnum_query = tk.Entry(frame_item, textvariable=self.num_query)
        txtnum_query.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

        tk.Label(frame_item, text='Подзадача', bg="#333333", fg="white", font=("Arial", 16)).grid(row=2,

                                                                                                  sticky="e")
        txtnum_task = tk.Entry(frame_item, textvariable=self.num_task)
        txtnum_task.grid(row=2, column=1, pady=5, padx=10, sticky="ew")

        tk.Label(frame_item, text='Часы', bg="#333333", fg="white", font=("Arial", 16)).grid(row=3,
                                                                                             sticky="e")
        tk.Entry(frame_item, textvariable=self.hours_var).grid(row=3, column=1, pady=5, padx=10, sticky="ew")

        tk.Label(frame_item, text='Дата регистрации', bg="#333333", fg="white", font=("Arial", 16)).grid(row=4,
                                                                                                         sticky="e")

        self.date_reg = DateEntry(master=frame_item, width=15, relief="solid", dateformat='%d-%m-%Y')
        self.date_reg.grid(row=4, column=1, pady=10, sticky="ew", padx=10)

        # Место для отображения результата входа
        self.result_label = tk.Label(frame_item, bg="#333333", fg="blue", font=("Arial", 10))
        self.result_label.grid(row=5, columnspan=2, sticky="ew")

        self.description = tk.Text(frame_item, height=5)
        self.description.grid(row=6, columnspan=2, sticky="ew")

        frame_buttons = tk.Frame(frame_item)
        tk.Button(frame_buttons, text=' Добавить ',
                  command=self.save_days,
                  bg="#FF3399", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_buttons, text=' Обновить ',
                  command=self.update_llk,
                  bg="#FF3399", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_buttons, text=' Удалить ',
                  command=self.delete_rec,
                  bg="red", fg="white", font=("Arial", 12)).pack(side=tk.LEFT)
        frame_buttons.grid(row=7, columnspan=2, pady=10)
        frame_item.pack()

    @property
    def read_all_params(self):
        days = self.hours_var.get()
        if days == 0:
            raise ValueError("Количество часов не может быть нулевым.")
        date_registration = datetime.strptime(self.date_reg.entry.get(), '%d-%m-%Y')
        # date_registration = self.date_reg.entry.get()
        month_date = date_registration.strftime("%m.%Y")
        quoter = Univunit.get_first_day_of_quarter(date_registration)
        query_hours = self.hours_var.get()
        num_task_ = self.num_task.get()
        # Если подзадача отсутствует или равна "0"
        if num_task_ == '' or num_task_ == '0':
            num_query = self.num_query.get()
            num_task = '0'
            first_input = query_hours
        else:
            first_input = 0
            num_task = self.num_query.get()
            num_query = self.num_task.get()
            # sum_query = query_hours + DB_MANAGER.get_summaryon_numbquery(num_task)
            DB_MANAGER.set_sum_numbquery(num_task, query_hours)

        description = self.description.get("1.0", tk.END).strip()  # Убираем лишние пробелы

        params = [
            {'num_query': num_query}, {'query_hours': query_hours}, {'quoter': quoter},
            {'num_task': num_task}, {'first_input': first_input}, {'month_date': month_date},
            {'date_registration': date_registration},
        ]
        if description:
            params.append({'description': description})

        return params

    def update_llk(self):
        try:
            params = self.read_all_params
            DB_MANAGER.update_lukoil(params)
            self.result_label.config(text=f" данные запроса {params[0]['num_query']} изменены")
            self.read_all_data()
        except ValueError as ve:
            messagebox.showinfo('Ошибка ввода', str(ve))
        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не сохранены: {e}")

    def read_all_data(self):
        # um_query, query_hours, date_registration, quoter, month_date, description
        DB_MANAGER.read_sum_lukoil()
        self.table_fte.configure_columns(
            [{'name': 'П/П'},{'name': 'Заявка'}, {'name': 'Подзадача'}, {'name': 'Часы'}, {'name': 'Регистрация'}, {'name': 'Квартал'},
             {'name': 'Месяц'},
             {'name': 'Содержание'}])
        data = DB_MANAGER.read_all_lukoil()
        # df = get_data_lukoil(data)

        self.table_fte.populate_table(data)
        # Привязываем обновление переменной num_query при выборе строки
        self.table_fte.tree.bind('<<TreeviewSelect>>', self.update_num_query)

    def update_num_query(self, event):
        """Обновляем переменную self.num_query при выборе строки в таблице."""
        self.description.delete("1.0", tk.END)  # очистка текстового поля
        cur_item = self.table_fte.tree.item(self.table_fte.tree.focus())  # Получаем данные выбранной строки
        if cur_item:
            values = cur_item.get('values', [])  # Получаем список значений
            if values:
                self.num_query.set(values[2])  # Устанавливаем значение первой колонки (Заявка)
                self.num_task.set(values[3])  # Устанавливаем значение первой колонки (Заявка)
                self.description.insert(tk.END, values[8])

    def delete_rec(self):
        try:
            num_query = self.num_query.get()
            DB_MANAGER.delete_num_query(num_query)
            self.result_label.config(text=f"Запрос {num_query} удален")

            self.read_all_data()
        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не сохранены: {e}")

    def save_days(self):
        try:
            days = self.hours_var.get()
            if days == 0:
                raise ValueError("Количество часов не может быть нулевым.")

            params = self.read_all_params
            DB_MANAGER.insert_lukoil(params)
            self.result_label.config(text=f" Запрос {params[0]['num_query']} добавлен")
            self.read_all_data()
        except ValueError as ve:
            messagebox.showinfo('Ошибка ввода', str(ve))
        except Exception as e:
            messagebox.showinfo('Ошибка с бд', f"Данные не сохранены: {e}")
