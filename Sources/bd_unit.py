# -*- coding: utf-8 -*-
from datetime import datetime
import sqlite3
from pathlib import Path
import logging
import pandas as pd

# import univunit
from univunit import (format_date)

DB_NAME = "test.db"
ICON_PATH = 'BD/analysis24.ico'


logging.basicConfig(
    filename='../app.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8'
)

logged = False


class DatabaseManager:
    def __init__(self):
        self.db_name = Path('./').absolute().joinpath('BD').joinpath(DB_NAME)

    def delete_record(self, date_month_name):
        """
        Удаление одной записи
        :param date_month_name:
        :return:
        """
        with sqlite3.connect(self.db_name) as conn:
            sql_delete_table = ("DELETE FROM main.tab_fte "
                                "where main.tab_fte.MONTH_NAME = ?;")
            conn.execute(sql_delete_table, (date_month_name,))

    def delete_num_query(self, num_query):
        """
        Удаление одной записи
        :return:
        """
        num_task = self.get_task_number(num_query)
        with sqlite3.connect(self.db_name) as conn:
            sql_delete_table = ("DELETE FROM main.tab_lukoil  "
                                "where main.tab_lukoil.num_query = ?;")
            conn.execute(sql_delete_table, (num_query,))

        self.set_sum_number_query_on_delete(num_query, num_task)

    def insert_data(self, list_params):
        """
        Вставка в таблицу
        :param list_params: [(,),(,)]
        :return: None
        """
        with sqlite3.connect(self.db_name) as conn:
            ins_sql = "INSERT INTO tab_fte (HOURS, MONTH_NAME) VALUES(?,?)"
            for par in list_params:
                conn.execute(ins_sql, par)
            conn.commit()

    def read_one_rec(self, ds, dp):
        # current_date = datetime.now()

        ds = datetime.strptime(ds, '%d-%m-%Y').date()
        dp = datetime.strptime(dp, '%d-%m-%Y').date()

        first_data_ds = ds.replace(day=1).strftime('%Y-%m-%d')
        first_data_dp = dp.replace(day=1).strftime('%Y-%m-%d')

        with sqlite3.connect(self.db_name) as conn:
            sql_read_table = ("SELECT SUM(HOURS) as hours "
                              "FROM main.tab_fte "
                              "WHERE main.tab_fte.MONTH_NAME >= ? and main.tab_fte.MONTH_NAME <= ?;")
            cursor = conn.execute(sql_read_table, (first_data_ds, first_data_dp))
            return cursor.fetchall()

    def read_sum_lukoil(self, **param):
        project = 'С0134-КИС "Производственный учет и отчетность"'
        user = 'Тапехин Алексей Александрович'
        if param:
            ss = "where date_registration >= ? and date_registration <= ?"
        else:
            ss = ""
        try:
            with sqlite3.connect(self.db_name) as conn:
                sql_read_table = (f"""select '{project}' as [Проект], '{user}' as [Пользователь], month_date as [Дата], 
                                        sum(sum(case when first_input >0
                                            then first_input
                                            else  query_hours
                                                end)) over (partition by t.num_query, month_date) as [Лукойл, час.],
                                        count(1) as [Заявок лукойл]                                    
                                    from tab_lukoil t
                                    {ss}
                                    group by   month_date""")

            if param:
                par = (
                    format_date(param['date_begin']),
                    format_date(param['date_end'])
                )
                cursor = conn.execute(sql_read_table, par)
            else:
                cursor = conn.execute(sql_read_table)
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=['Проект', 'Пользователь', 'Дата', 'Лукойл, час.', 'Заявок лукойл'])
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")

        #  --and first_input > 0

    def read_all_lukoil(self, **param):
        if param:
            ss = "where date_registration >= ? and date_registration <= ?"
        else:
            ss = ""
        try:
            with sqlite3.connect(self.db_name) as conn:
                sql_read_table = (
                    f"""
                    SELECT floor(CASE
                     WHEN ((julianday(date_registration) - julianday(DATE(date_registration, 'start of month'))) / 7) + 1 >=
                          5 THEN 4
                     ELSE ((julianday(date_registration) - julianday(DATE(date_registration, 'start of month'))) / 7) + 1
                        END)                                                                                        AS [Неделя],
                           row_number() over (partition by case when num_task = 0 then num_query else num_task end) as pp,
                           num_query,
                           num_task,
                           query_hours,
                           date_registration,
                           quoter,
                           month_date,
                           description                
                    FROM tab_lukoil               
                        {ss}                       
                    order by case when num_task = 0 then num_query else num_task end, date_registration
                    """
                )
            if param:
                par = (
                    format_date(param['date_begin']),
                    format_date(param['date_end'])
                )
                cursor = conn.execute(sql_read_table, par)
            else:
                cursor = conn.execute(sql_read_table)
            rows = cursor.fetchall()
            return rows
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")

    def read_all_table(self):
        with sqlite3.connect(self.db_name) as conn:
            sql_read_table = "SELECT  MONTH_NAME, HOURS FROM tab_fte order by MONTH_NAME;"
            cursor = conn.execute(sql_read_table)
            rows = cursor.fetchall()
            return rows

    def get_summaryon_numbquery(self, num_query):
        with sqlite3.connect(self.db_name) as conn:
            sql_read_table = ("select sum(case when num_task= ? then query_hours else 0 end) "
                              "+  sum(case when num_query= ? then first_input else 0 end) as qh_ "
                              "from tab_lukoil t where  ? in (num_task,num_query)")

            cursor = conn.execute(sql_read_table, (num_query, num_query, num_query,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def set_sum_numbquery(self, num_query, query_hours):
        sum_query = query_hours + self.get_summaryon_numbquery(num_query)
        with sqlite3.connect(self.db_name) as conn:
            sql = "update main.tab_lukoil set query_hours = ? where num_query = ?;"
            params = (sum_query, num_query)
            conn.execute(sql, params)
            conn.commit()

    def get_task_number(self, num_query):
        with sqlite3.connect(self.db_name) as conn:
            sql_read_table = "SELECT num_task FROM tab_lukoil WHERE num_query=?"
            cursor = conn.execute(sql_read_table, (num_query,))
            row = cursor.fetchone()  # Получаем только одну строку
        return row[0] if row else None

    def set_sum_number_query_on_delete(self, num_query, num_task):

        if num_task:
            num_query = num_task

        sum_query = self.get_summaryon_numbquery(num_query)

        if sum_query:
            with sqlite3.connect(self.db_name) as conn:
                if num_task:
                    sql = "update main.tab_lukoil set query_hours = ? where num_query = ?;"
                else:
                    sql = "update main.tab_lukoil set query_hours = first_input where num_query = ?;"
                params = (sum_query, num_query)
                conn.execute(sql, params)
                conn.commit()

    def update_lukoil(self, param_list):
        """
        Динамический sql
        :param_list param_list:
        :return:
        """
        params = {}
        for param in param_list:
            params.update(param)

            # Проверяем, что 'num_query' передан, так как он нужен для условия WHERE
        if 'num_query' not in params:
            raise ValueError("Необходимо передать 'num_query' для обновления записи.")

            # Извлекаем num_query для условия WHERE
        num_query = params.pop('num_query')

        # Подготовка динамических полей для обновления и их значений
        set_clauses = []
        values = []

        for key, value in params.items():
            set_clauses.append(f"{key} = ?")  # Используем плейсхолдеры для безопасности
            values.append(value)

        # Формирование SQL-запроса
        sql_update_lukoil = f"UPDATE tab_lukoil SET {', '.join(set_clauses)} WHERE num_query = ?;"

        # Добавляем num_query в список значений для условия WHERE
        values.append(num_query)

        # Выполнение запроса (предполагается использование подключения к базе данных, например, sqlite3)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(sql_update_lukoil, values)
            conn.commit()

    def insert_lukoil(self, param_list):
        # Создаем пустой словарь для объединения всех параметров
        params = {}

        # Обрабатываем список словарей и добавляем ключи-значения в общий словарь params
        for param in param_list:
            params.update(param)

        # Если нет параметров, нет смысла выполнять запрос
        if not params:
            if logged:
                logging.error(f"Параметры для вставки должны быть переданы.")
            raise ValueError("Параметры для вставки должны быть переданы.")

        # Извлечение ключей и значений из словаря params
        columns = ', '.join(params.keys())  # Имена колонок
        placeholders = ', '.join(['?' for _ in params])  # Плейсхолдеры для значений
        values = list(params.values())  # Список значений для вставки

        # Формирование SQL-запроса для вставки
        sql_insert_lukoil = f"INSERT INTO tab_lukoil ({columns}) VALUES ({placeholders});"
        if logged:
            logging.info(f"Executing SQL: {sql_insert_lukoil} with values {values}")

        # Выполнение запроса (предполагается использование подключения к базе данных, например, sqlite3)
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(sql_insert_lukoil, values)
                conn.commit()
        except sqlite3.DatabaseError as e:
            if logged:
                logging.error(f"Database error occurred: {e}")
            raise e
        return

    def get_middle_fte(self):
        with sqlite3.connect(self.db_name) as conn:
            sql_read_table = "SELECT VALUE_STR FROM tab_settings where PROPERTY ='middle_fte' "
            cursor = conn.execute(sql_read_table)
            row = cursor.fetchone()  # Получаем только одну строку
        return row[0] if row else '0'

    def save_middle_fte(self, middle_fte):
        fte = self.get_middle_fte()
        with sqlite3.connect(self.db_name) as conn:
            if fte == '0':
                sql = "INSERT INTO tab_settings (PROPERTY,VALUE_STR) VALUES(?,?)"
                conn.execute(sql, ('middle_fte', middle_fte))
            else:
                sql = "update tab_settings set VALUE_STR= ? where PROPERTY=?"
                conn.execute(sql, (middle_fte, 'middle_fte'))
            conn.commit()
