import unittest
import pandas as pd


# Путь к Excel-файлу
file_path = ("C:\\Яндекс\\pro\\PythonPro\\Iteco\\Analiz\\Analiz\\Sources\\2 квартал\\"
             "Сводный список запросов - 2024 апрель.xlsx")

# Для получения минимальной и максимальной даты
date_column = "Дата регистрации"
# Название столбца, в котором нужно искать CRQ
check_column = "Номер запроса"
status_column = "Статус"
request_type_column = "Тип запроса"
registered_column = "Зарегистрировано в период"
complete_period = "Выполнено в период"
complete_prosr = "Выполнено с просрочкой в период"
open_end_prosr = "Открыто на конец периода с просрочкой"
open_prosr = "Просрочено в период"
open_begin = "Открыто на начало периода"
open_end = "Открыто на конец периода"
rem_err_sla = "Комментарий к нарушению SLA"
time_reactions="Просроченное время реакции, часов"
time_solved ="Просроченное время решения, часов"

class TestExcelData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Загрузка данных из файла Excel с учетом строки заголовка
        cls.df = pd.read_excel(file_path, header=2 , engine='openpyxl')  # Заголовок начинается с третьей строки

    def test_date_column_exists(self):
        """Проверка, что столбец с датами существует."""
        self.assertIn(date_column, self.df.columns, f"Столбец '{date_column}' не найден в файле.")

    # def test_min_max_date(self):
    #     """Проверка минимальной и максимальной даты в столбце дат."""
    #     # Преобразование столбца к типу даты
    #     df_dates = pd.to_datetime(self.df[date_column], errors='coerce').dropna()
    #
    #     # Нахождение минимальной и максимальной даты
    #     min_date = df_dates.min()
    #     max_date = df_dates.max()
    #
    #     # Проверка, что минимальная дата меньше или равна максимальной
    #     self.assertLessEqual(min_date, max_date, "Минимальная дата не должна быть больше максимальной")
    #     print(f"Минимальная дата: {min_date}")
    #     print(f"Максимальная дата: {max_date}")

    def test_inc_count(self):
        """Проверка, что количество строк, содержащих INC' (без учета строк со статусом 'отмена'), равно 10."""
        # Проверка наличия столбцов

        inc_integr = 0

        self.assertIn(check_column, self.df.columns, f"Столбец '{check_column}' не найден в файле.")
        self.assertIn(status_column, self.df.columns, f"Столбец '{status_column}' не найден в файле.")

        # Фильтрация строк: исключаем строки со статусом "отмена"
        filtered_df = self.df[~self.df[status_column].astype(str).str.contains("Отменено", case=False, na=False)]
        # print(self.df.shape[0])
        # print(filtered_df.shape[0])

        # Фильтрация по датам (между начальной и конечной датой периода)
        df_dates = pd.to_datetime(filtered_df[date_column], errors='coerce').dropna()
        end_date = df_dates.max()
        start_date = "2024-04-01"
        filtered_df[date_column] = pd.to_datetime(filtered_df[date_column], errors='coerce')
        date_filtered_df = filtered_df[
            (filtered_df[date_column] >= start_date) & (filtered_df[date_column] <= end_date)]
        print(f"date_filtered_df= {date_filtered_df.shape[0]}")
        # Подсчет строк, содержащих "CRQ" в отфильтрованных данных
        crq_count = filtered_df[check_column].astype(str).str.contains("CRQ", case=False, na=False).sum()
        inc_count = filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False).sum()
        inc_data = filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False)
        # inc_data = date_filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False)
        # print(f"crq_count= {crq_count}")
        # print(f"inc_data= {inc_data.shape[0]}")

        # print(end_date)
        # Суммирование значений по столбцам

        inc_registered_sum = filtered_df[inc_data][registered_column].sum()
        inc_complete_sum = filtered_df[inc_data][complete_period].sum()
        inc_complete_prosr_sum = filtered_df[inc_data][complete_prosr].sum()
        inc_open_end_prosr_sum = filtered_df[inc_data][open_end_prosr].sum()
        inc_open_begin_sum = filtered_df[inc_data][open_begin].sum()

        # EscM  вычисляется  как отношение числа заявок, неверно эскалированных на следующую рабочую группу
        # в ИС Сервис, к общему количеству заявок по услуге.
        # Доля ошибок эскалации {inc_err_esk_sum}

        # Фильтрация по inc_data, чтобы применить одинаковые индексы
        inc_data_filtered = date_filtered_df[inc_data]

        print(f"inc_data_filtered= {inc_data_filtered.shape[0]}")
        # Подсчет строк, содержащих "03. Changing" в столбце "rem_err_sla" для "INC"
        incorrect_count_esc = inc_data_filtered[rem_err_sla].astype(str).str.contains("02. incorrect", case=False,
                                                                                      na=False).sum()

        incorrect_count_cat = inc_data_filtered[rem_err_sla].astype(str).str.contains("03. Changing", case=False,
                                                                                      na=False).sum()


        # # Подсчет строк, содержащих "02. incorrect" в столбце "Комментарий" для "INC"
        # incorrect_count_esc = date_filtered_df[inc_data][rem_err_sla].astype(str).str.contains("02. incorrect",
        #                                                                                        case=False,
        #                                                                                        na=False).sum()
        # incorrect_count_cat = date_filtered_df[inc_data][rem_err_sla].astype(str).str.contains("03. Changing",
        #                                                                                        case=False,
        #                                                                                        na=False).sum()
        inc_err_esk_sum = round(incorrect_count_esc / inc_data.count(), 2)
        inc_err_cat_sum = round(incorrect_count_cat / inc_data.count(), 2)



        # Применяю период с 1 го числа
        # inc_reg_period_sum = pd.to_numeric(date_filtered_df[inc_data][registered_column], errors='coerce').sum()

        # Сначала отфильтруем строки с помощью inc_data, чтобы создать подмножество с совпадающими индексами
        # inc_data_filtered = date_filtered_df[inc_data]

        # Затем применим операцию с нужным столбцом, уже без предупреждений о несоответствии индексов
        inc_reg_period_sum = pd.to_numeric(inc_data_filtered[registered_column], errors='coerce').sum()


        # Подсчет строк, содержащих "INC" в отфильтрованных данных
        inc_count = inc_data.sum()

        # Дополнительный фильтр для "INC" с учетом столбца "Тип запроса" со значением "Инцидент"
        incident_data = filtered_df[(filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False)) &
                                    (filtered_df[request_type_column] == "Инцидент")]

        inc_incident_count = incident_data.shape[0]
        inc_incident_prosr_count = incident_data[incident_data["Просрочено в период"] == '1'].shape[0]
        # inc_open_end_prosr_sum = 0
        SLA = round(
            (1 - (inc_complete_prosr_sum + inc_open_end_prosr_sum) / (inc_open_begin_sum + inc_reg_period_sum)) * 100,
            0)
        if SLA >= 98:
            inc_integr = 1

        # Проверка количества "CRQ", общего количества "INC", количества "INC" с типом "Инцидент" и суммы для "INC"
        self.assertEqual(crq_count, 10, f"Ожидалось 10 строк с 'CRQ' (без учета 'отмена'), но найдено {crq_count}")
        self.assertEqual(inc_count, 51, f"Ожидалось 51 строка с 'INC' (без учета 'отмена'), но найдено {inc_count}")
        self.assertEqual(inc_incident_count, 6,
                         f"Ожидалось 6 строк с 'INC' и 'Инцидент' (без учета 'отмена'), но найдено {inc_incident_count}")
        self.assertEqual(inc_registered_sum, 48,
                         f"Ожидалось, что сумма значений 'Зарегистрировано в период' для 'INC' "
                         f"(без учета 'отмена') будет равна 48, но получилось {inc_registered_sum}")

        self.assertEqual(inc_complete_sum, 42,
                         f"Ожидалось, что сумма значений {complete_period} для 'INC' "
                         f"(без учета 'отмена') будет равна 42, но получилось {inc_complete_sum}")

        self.assertEqual(inc_incident_prosr_count, 0, f"Ожидалось, что Ицидент с просрочкой  "
                                                      f"(без учета 'отмена') будет равен 0, но получилось {inc_incident_prosr_count}")

        self.assertEqual(inc_complete_prosr_sum, 1, f"Ожидалось, что выполнено с просрочкой в период "
                                                    f"(без учета 'отмена') будет равен 1, но получилось {inc_complete_prosr_sum}")

        self.assertEqual(inc_open_end_prosr_sum, 1, f"Ожидалось, что открыто с просрочкой на конец периода "
                                                    f"(без учета 'отмена') будет равен 1, но получилось {inc_open_end_prosr_sum}")

        self.assertEqual(inc_open_begin_sum, 3, f"Ожидалось, что открыто на начало периода "
                                                f"(без учета 'отмена') будет равен 3, но получилось {inc_open_begin_sum}")

        self.assertEqual(inc_reg_period_sum, 48,
                         f"Ожидалось, что сумма значений 'Зарегистрировано в период' для 'INC' "
                         f"(без учета 'отмена') будет равна 48, но получилось {inc_reg_period_sum}")

        # print(f"Количество строк с 'CRQ' (без учета 'отмена'): {crq_count}")
        # print(f"Количество строк с 'INC' (без учета 'отмена'): {inc_count}")
        data = {
            "1 Общее количество зарегистрированных заявок": inc_registered_sum,
            "2 Общее количество выполненных заявок": inc_complete_sum,
            "3 Общее количество зарегистрированных заявок за отчетный период, имеющих категорию «Инцидент»)": inc_incident_count,
            "4 Количество заявок за период с превышением срока выполнения, имеющих категорию «Инцидент»": inc_incident_prosr_count,
            "5 Количество заявок за период с превышением времени реакции по поддержке": 0,
            "6 tur1 Количество закрытых заявок на поддержку с нарушением сроков заявок": inc_complete_prosr_sum,
            "7 tur2 Количество незакрытых заявок, с нарушением срока": inc_open_end_prosr_sum,
            "8 tur3 Количество перешедших с прошлого периода заявок на поддержку": inc_open_begin_sum,
            "9 TUR4 Количество заявок, зарегистрированных в отчетном периоде": inc_reg_period_sum,
            "10  EscM Доля ошибок эскалации": inc_err_esk_sum,
            "11  CatM Доля ошибок категоризации": inc_err_cat_sum,
            "12  Интегральный показатель качества оказания услуг по поддержке": inc_integr,
            "Интегральный показатель качества оказания услуг по поддержке % ": SLA
        }

        prnt(data)

    def test_crq_count(self):
        crq_integr = 0

        self.assertIn(check_column, self.df.columns, f"Столбец '{check_column}' не найден в файле.")
        self.assertIn(status_column, self.df.columns, f"Столбец '{status_column}' не найден в файле.")

        # Фильтрация строк: исключаем строки со статусом "отмена"
        filtered_df = self.df[~self.df[status_column].astype(str).str.contains("Отменено", case=False, na=False)]

        # Фильтрация по датам (между начальной и конечной датой периода)
        df_dates = pd.to_datetime(filtered_df[date_column], errors='coerce').dropna()
        end_date = df_dates.max()
        start_date = "2024-04-01"

        date_filtered_df = filtered_df[
            (filtered_df[date_column] >= start_date) & (filtered_df[date_column] <= end_date)]

        # Подсчет строк, содержащих "CRQ" в отфильтрованных данных
        crq_data = filtered_df[check_column].astype(str).str.contains("CRQ", case=False, na=False)
        crq_count = crq_data.sum()

        # Суммирование значений по столбцам

        crq_registered_sum = filtered_df[crq_data][registered_column].sum()
        crq_complete_sum = filtered_df[crq_data][complete_period].sum()
        crq_complete_prosr_sum = filtered_df[crq_data][complete_prosr].sum()
        crq_open_end_sum = filtered_df[crq_data][open_end].sum()
        # 6 если более 8 часов
        crq_reactions_sum = filtered_df[crq_data][time_reactions].sum()
        # 7 если не указан срок выполнения - то 12 часов
        crq_solved_sum = filtered_df[crq_data][time_solved].sum()
        # crq_open_end_prosr_sum = filtered_df[crq_data][open_end_prosr].sum()
        crq_open_begin_sum = filtered_df[crq_data][open_begin].sum()
        sla = round(100 * (crq_complete_sum - crq_complete_prosr_sum) / crq_complete_sum,0)
        if sla >= 98:
            crq_integr = 1

        self.assertEqual(crq_open_begin_sum, 4, f"Ожидалось, что открыто на начало периода "
                                                f"(без учета 'отмена') будет равен 4, но получилось {crq_open_begin_sum}")

        self.assertEqual(crq_registered_sum, 6,
                         f"Ожидалось, что сумма значений 'Зарегистрировано в период' для 'CRQ' "
                         f"(без учета 'отмена') будет равна 6, но получилось {crq_registered_sum}")

        self.assertEqual(crq_complete_sum, 9,
                         f"Ожидалось, что сумма значений {complete_period} для 'CRQ' "
                         f"(без учета 'отмена') будет равна 9, но получилось {crq_complete_sum}")

        self.assertEqual(crq_complete_prosr_sum, 0, f"Ожидалось, что выполнено с просрочкой в период "
                                                    f"(без учета 'отмена') будет равен 0, но получилось {crq_complete_prosr_sum}")

        self.assertEqual(crq_open_end_sum, 1, f"Ожидалось,5 что  Общее количество незакрытых заявок "
                                              f"по сопровождению на конец периода будет равен 1, но получилось {crq_open_end_sum}")

        # # Проверка количества "CRQ", общего количества "INC", количества "INC" с типом "Инцидент" и суммы для "INC"
        # self.assertEqual(crq_count, 10, f"Ожидалось 10 строк с 'CRQ' (без учета 'отмена'), но найдено {crq_count}")
        #
        # self.assertEqual(inc_incident_count, 6,
        #                  f"Ожидалось 6 строк с 'INC' и 'Инцидент' (без учета 'отмена'), но найдено {inc_incident_count}")

        #

        #
        # self.assertEqual(inc_incident_prosr_count, 0, f"Ожидалось, что Ицидент с просрочкой  "
        #                                               f"(без учета 'отмена') будет равен 0, но получилось {inc_incident_prosr_count}")
        #

        #
        # self.assertEqual(inc_open_end_prosr_sum, 1, f"Ожидалось, что открыто с просрочкой на конец периода "
        #                                             f"(без учета 'отмена') будет равен 1, но получилось {inc_open_end_prosr_sum}")
        #

        #
        # self.assertEqual(inc_reg_period_sum, 48,
        #                  f"Ожидалось, что сумма значений 'Зарегистрировано в период' для 'INC' "
        #                  f"(без учета 'отмена') будет равна 48, но получилось {inc_reg_period_sum}")

        # print(f"Количество строк с 'CRQ' (без учета 'отмена'): {crq_count}")
        # print(f"Количество строк с 'INC' (без учета 'отмена'): {inc_count}")
        data = {
            "1 tur3 Общее количество незакрытых заявок по сопровождению на начало периода": crq_open_begin_sum,
            "2 tur4 Общее количество зарегистрированных заявок по сопровождению за отчетный период": crq_registered_sum,
            "3 Общее количество закрытых за период заявок по сопровождению": crq_complete_sum,
            "4 tur1 Общее количество закрытых за период заявок по сопровождению c нарушением SLA": crq_complete_prosr_sum,
            "5 Общее количество незакрытых заявок по сопровождению на конец периода": crq_open_end_sum,

            "6 tur2 Количество заявок за период с превышением времени реакции по сопровождению": crq_reactions_sum,
            "7 Количество заявок за период с превышением срока выполнения по сопровождению": crq_solved_sum,
            "8 Количество заявок за период с превышением времени диспетчеризации": 0,
            "9 Уровень исполнения SLA": sla,
            "10  Интегральный показатель качества оказания услуг по сопровождению": crq_integr
        }

        prnt(data)


def prnt(data):
    for key, val in data.items():
        print(f"{key} = {val}")


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
