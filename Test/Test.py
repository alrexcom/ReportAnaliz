import datetime
import logging
import sqlite3
import unittest


# Установка адаптера для datetime
def adapt_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def convert_datetime(text):
    return datetime.datetime.strptime(text, '%Y-%m-%d %H:%M:%S')


sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

logging.basicConfig(
    filename='app.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8'
)

logged = False


# def updated_data_lukoil(update_lukoil):
#     def wrap_fn(self, *args, **kwargs):
#         print('before update')
#         update_lukoil(self, *args, **kwargs)
#         print('after update')
#
#     return wrap_fn

# def update_sum(self, *param_list):
#     test = param_list[0]['test']
#
#     if not test:
#         par = [{'num_query': 'num_query', 'query_hours': 0, }]
#         self.update_lukoil(par)


def dec_insert_lukoil(insert_lukoil):
    def wrap_fn(self, *args, **kwargs):
        # print(f"action before: {args, kwargs}", insert_lukoil.__name__)
        num_query = insert_lukoil(self, *args, **kwargs)
        # test = args[0]['test']
        print(f"after insert {num_query} ")

        # if test == True:
        par = [{'num_query': 'num_query', 'query_hours': 0, }]
        self.update_lukoil(par)
        # return result

    return wrap_fn


class YourClass:
    def __init__(self, conn):
        self.conn = conn  # Используем постоянное соединение с базой данных

    def read_all_table(self):
        cur = self.conn.cursor()
        try:
            sql_read_table = "SELECT  * FROM tab_lukoil order by date_registration;"
            cursor = cur.execute(sql_read_table)
            rows = cursor.fetchall()
            if logged:
                for row in rows:
                    logging.info(f"select  *: {row} ")

        finally:
            cur.close()

    def get_sum(self, num_query):
        cur = self.conn.cursor()
        try:
            # print(1)
            sql_read_table = (
                'select count(1) as kol, sum(case when first_input>0 then first_input else query_hours end) as sum,'
                'max(num_task) as num_task, max(num_query) as num_query '
                'from tab_lukoil where ? in (num_query, num_task)')

            # if logged:
            #     logging.info(f"summa: {sql_read_table} \n num:{num_query} ")

            cur.execute(sql_read_table, (num_query,))
            sum_query_hours = cur.fetchone()

        finally:
            cur.close()
        logging.info(f"summa: {sum_query_hours} ")
        return sum_query_hours

    # @updated_data_lukoil
    def update_lukoil(self, param_list):
        """
        Динамический sql
        :param_list param_list:
        :return:
        """
        self.read_all_table()

        params = {}
        for param in param_list:
            params.update(param)

        # Проверяем, что 'num_query' передан, так как он нужен для условия WHERE
        if 'num_query' not in params:
            raise ValueError("Необходимо передать 'num_query' для обновления записи.")

        if logged:
            logging.info(f"paramDO: {params}  ")

        num_query = params.pop('num_query')
        results = self.get_sum(num_query)

        if 'CRQ' in num_query:
            # 1 запись crq
            if results[0] == 1:
                if params['query_hours'] == 0:
                    params['query_hours'] = results[1]
                    params['first_input'] = results[1]
                params['first_input'] = params['query_hours']
            else:
                params['query_hours'] = results[1]

        if logged:
            logging.info(f"param_list: {params}  ")

        set_clauses = []
        values = []

        for key, value in params.items():
            set_clauses.append(f"{key} = ?")  # Используем плейсхолдеры для безопасности
            values.append(value)

        # Формирование SQL-запроса
        sql_update_lukoil = f"UPDATE tab_lukoil SET {', '.join(set_clauses)} WHERE num_query = ?;"

        values.append(num_query)

        # self.read_all_table()

        if logged:
            logging.info(f"update: {sql_update_lukoil} \n значения {values} ")
        # Выполнение запроса
        self.conn.execute(sql_update_lukoil, values)
        self.conn.commit()

        # self.read_all_table()

    @dec_insert_lukoil
    def insert_lukoil(self, param_list):
        # Создаем пустой словарь для объединения всех параметров
        values = []
        if not param_list:
            raise ValueError("Параметры для вставки должны быть переданы.")
        # test = param_list_[0]['test']


        # Обрабатываем список словарей и добавляем ключи-значения в общий словарь params
        for params in param_list:

            # Если нет параметров, нет смысла выполнять запрос
            if not params:
                raise ValueError("Параметры для вставки должны быть переданы.")

            if 'CRQ' in params['num_query']:
                params['first_input'] = params['query_hours']
                num_query = params['num_query']
            else:
                params['first_input'] = 0
                num_query = params['num_task']

            columns = ', '.join(params.keys())  # Имена колонок
            placeholders = ', '.join(['?' for _ in params])  # Плейсхолдеры для значений

            # Преобразуем даты в строки для корректной вставки
            for key, value in params.items():
                if isinstance(value, datetime.datetime):
                    params[key] = value  # Здесь мы используем адаптер

            values.append(tuple(params.values()))

            sql_insert_lukoil = f"INSERT INTO tab_lukoil ({columns}) VALUES ({placeholders});"

            # if logged:
            #     logging.info(f"SQL:{sql_insert_lukoil} insert with values {values}")

        self.conn.executemany(sql_insert_lukoil, values)
        self.conn.commit()
        return num_query
        # return [{'num_query': num_query, 'query_hours': 0, 'test': test}]

        # insert_lukoil = dec_insert(insert_lukoil)  # Явно применяем декоратор

        #
        # par = [{'num_query': num_query, 'query_hours': 0, }]
        # if not test:
        #     self.update_lukoil(par)


def initdata(mumber_position=1):
    """Тестирование обновления данных в таблице"""
    # Вставляем начальные данные
    data = []
    test_data1 = {
        'num_query': 'CRQ000000849982', 'query_hours': 10, 'quoter': '01-10-2024',
        'date_registration': datetime.datetime(2024, 10, 18, 0, 0),
        'month_date': '10.2024', 'description': '10', 'num_task': '0'
    }
    test_data2 = {
        'num_query': 'TASK00005', 'query_hours': 5, 'quoter': '01-10-2024',
        'date_registration': datetime.datetime(2024, 10, 19, 0, 0),
        'month_date': '10.2024', 'description': '15', 'num_task': 'CRQ000000849982'
    }
    test_data3 = {
        'num_query': 'TASK00006', 'query_hours': 15, 'quoter': '01-10-2024',
        'date_registration': datetime.datetime(2024, 10, 20, 0, 0),
        'month_date': '10.2024', 'description': '30', 'num_task': 'CRQ000000849982'
    }

    if mumber_position == 1:
        # Вставляем данные с помощью метода insert_lukoil
        data.append(test_data1)

    elif mumber_position == 2:
        data.append(test_data1)
        data.append(test_data2)

    elif mumber_position == 3:
        data.append(test_data1)
        data.append(test_data2)
        data.append(test_data3)
    return data


def updated_data(number_position=1):
    if number_position == 1:
        return {'num_query': 'CRQ000000849982', 'query_hours': '15',
                'date_registration': datetime.datetime(2024, 10, 20, 0, 0)}
    elif number_position == 2:
        return {'num_query': 'TASK00005', 'query_hours': '15'}


def get_expected_results(mumber_position=1):
    expected_results = []
    if mumber_position == 1:
        expected_results = [
            ('CRQ000000849982', 10, '01-10-2024', '2024-10-18 00:00:00', '10.2024', '10', '0', 10), ]
    elif mumber_position == 2:
        expected_results = [
            ('CRQ000000849982', 15, '01-10-2024', '2024-10-18 00:00:00', '10.2024', '10', '0', 10),
            ('TASK00005', 5, '01-10-2024', '2024-10-19 00:00:00', '10.2024', '15', 'CRQ000000849982', 0), ]
    elif mumber_position == 3:
        expected_results = [
            ('CRQ000000849982', 30, '01-10-2024', '2024-10-18 00:00:00', '10.2024', '10', '0', 10),
            ('TASK00005', 5, '01-10-2024', '2024-10-19 00:00:00', '10.2024', '15', 'CRQ000000849982', 0),
            ('TASK00006', 15, '01-10-2024', '2024-10-20 00:00:00', '10.2024', '30', 'CRQ000000849982', 0)
        ]
    elif mumber_position == 4:
        expected_results = [
            ('CRQ000000849982', 15, '01-10-2024', '2024-10-20 00:00:00', '10.2024', '10', '0', 15),
        ]
    elif mumber_position == 5:
        expected_results = [
            ('CRQ000000849982', 25, '01-10-2024', '2024-10-18 00:00:00',
             '10.2024', '10', '0', 10),
            ('TASK00005', 15, '01-10-2024', '2024-10-19 00:00:00',
             '10.2024', '15', 'CRQ000000849982', 0),
        ]

    # expected_result = [
    #     ('CRQ000000849982', 55, '01-10-2024', '2024-10-18 00:00:00',
    #      '10.2024', '10+5+15', '0', 10),
    #     # ('TASK00005', 5, '01-10-2024', '2024-10-19 00:00:00',
    #     #  '10.2024', '15', 'CRQ000000849982', 0),
    #     # ('TASK00006', 15, '01-10-2024', '2024-10-20 00:00:00',
    #     #  '10.2024', '30', 'CRQ000000849982', 0)
    # ]

    return expected_results


class TestActionsLukoil(unittest.TestCase):

    def setUp(self):
        """Инициализация временной базы данных и создание тестовой таблицы"""
        self.conn = sqlite3.connect(':memory:')  # Используем одно постоянное соединение
        self.obj = YourClass(self.conn)

        # Создаем таблицу для тестов
        self.create_table()
        self.clear_table()  # Очищаем таблицу перед каждым тестом

    def clear_table(self):
        """Очищает таблицу перед каждым тестом"""
        cursor = self.conn.cursor()
        cursor.execute("delete from tab_lukoil;")
        self.conn.commit()

    def tearDown(self):
        """Закрываем соединение с базой данных после тестов"""
        self.conn.close()

    def create_table(self):
        """Функция для создания таблицы"""
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tab_lukoil
                (
                    num_query         TEXT    NOT NULL
                        CONSTRAINT tab_lukoil_pk
                            PRIMARY KEY,
                    query_hours       INTEGER NOT NULL,
                    quoter            TEXT    NOT NULL,
                    date_registration DATETIME,
                    month_date        TEXT,
                    description       TEXT,
                    num_task          TEXT,
                    first_input       INTEGER
                );
        ''')
        self.conn.commit()

    def check_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT num_query, query_hours, quoter, date_registration, month_date, description, "
                       "        num_task, first_input  "
                       "FROM tab_lukoil order by date_registration")
        results = cursor.fetchall()

        cursor.close()
        return results

    def check_insert_result(self, number_position_):
        data_ = initdata(mumber_position=number_position_)
        self.obj.insert_lukoil(data_)
        expected_results = get_expected_results(mumber_position=number_position_)
        self.assertEqual(self.check_data(), expected_results)

    def test_insert_lukoil1(self):
        """Вставка первой записи"""
        self.check_insert_result(number_position_=1)

    def test_insert_lukoil2(self):
        """вставка 2 записей"""
        self.check_insert_result(number_position_=2)

    def test_insert_lukoil3(self):
        """вставка 3 записей"""
        self.check_insert_result(number_position_=3)

    def test_update_lukoil1(self):
        """
        Обновление 1 записи
        """

        data_ = initdata(mumber_position=1)

        self.obj.insert_lukoil({'data': data_, 'test': False})

        updated_data_ = updated_data(number_position=1)

        self.obj.update_lukoil([updated_data_])

        # Проверяем, что данные обновлены

        expected_result = get_expected_results(mumber_position=4)

        self.assertEqual(self.check_data(), expected_result)

    def test_empty_param_list(self):
        """Тест пустого списка параметров"""
        with self.assertRaises(ValueError):
            self.obj.insert_lukoil([])

    def test_update_lukoil2(self):
        """
        Обновление второй записи
        """
        data_ = initdata(mumber_position=2)

        # print(data_)
        self.obj.insert_lukoil({'data': data_, 'test': True})

        updated_data_ = updated_data(number_position=2)

        # print(f"Обновляем {updated_data_}")
        self.obj.update_lukoil([updated_data_])

        # self.obj.update_lukoil([{'num_query': 'CRQ000000849982', 'query_hours': 0}])

        expected_result = get_expected_results(mumber_position=5)
        # if not params['num_task'] == '0':
        #     self.update_lukoil([{'num_query': params['num_task'], 'query_hours': 0}])
        self.assertEqual(self.check_data(), expected_result)


if __name__ == '__main__':
    unittest.main()
