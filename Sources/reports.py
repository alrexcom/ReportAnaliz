# -*- coding: utf-8 -*-
# import pandas as pd
from datetime import datetime, timedelta

import numpy as np

from univunit import (Univunit, pd)
# , save_to_json)
import bd_unit

DB_MANAGER = bd_unit.DatabaseManager()

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
time_reactions = "Просроченное время реакции, часов"
time_solved = "Просроченное время решения, часов"

REPORTS = [
    {
        "name": "Отчёт Данные по ресурсным планам и списанию трудозатрат сотрудников за период",
        "header_row": 0,
        "reportnumber": 1,
        "data_columns": ["Дата"]
    },
    {
        "name": "Контроль заполнения факта за период",
        "header_row": 1,
        "reportnumber": 2,
        "data_columns": ["Дата"]
    },
    {
        "name": "Сводный список запросов  для SLA (Сопровождение)  С0134-КИС",
        "header_row": 2,
        "reportnumber": 3,
        "data_columns": ["Дата регистрации", "Крайний срок решения", "Дата решения", "Дата закрытия",
                         "Дата последнего назначения в группу"],
        "status": ["В ожидании", "Выполнено", "Закрыто", "Проект изменения", "Решен", "Назначен", "Выполняется",
                   "Планирование изменения", "Выполнение изменения", "Экспертиза решения", "Согласование изменения",
                   "Автроизация изменения"],  # Отмена  убрано
        "support": False
    },
    {
        "name": "Сводный список запросов  для SLA (Поддержка) Т0133-КИС",
        "header_row": 2,
        "reportnumber": 4,
        "data_columns": ["Дата регистрации", "Крайний срок решения", "Дата решения", "Дата закрытия",
                         "Дата последнего назначения в группу"],
        "status": ["В ожидании", "Выполнено", "Закрыто", "Проект изменения", "Решен", "Назначен", "Выполняется",
                   "Планирование изменения", "Выполнение изменения", "Экспертиза решения", "Согласование изменения",
                   "Автроизация изменения"],  # Отмена  убрано
        "support": True
    },
    {
        "name": "Лукойл: Отчет по запросам и задачам (долго открывается)",
        "reportnumber": 5,
        "header_row": 3,
        "data_columns": ["Дата Выполнения работ", "Время назначения задачи"],
        "headers": ['ID инцидента/ЗИ', 'Исполнитель  по задаче', 'Трудозатраты по задаче (десят. часа)',
                    'Время назначения задачи', 'Категория инцидента', 'Статус', 'Содержание задачи'],
        'order by': 'Исполнитель  по задаче'
    },

]


def report1(**param):
    """
    Отчёт Данные по ресурсным планам и списанию трудозатрат сотрудников за период

    """

    df = param['df']



    date_begin = datetime.strptime(param['date_begin'], '%Y-%m-%d').strftime('%m.%Y')
    date_end = datetime.strptime(param['date_end'], '%Y-%m-%d').strftime('%m.%Y')

    df = df[(df['Дата'] >= date_begin) & (df['Дата'] <= date_end)]

    df_lukoil = DB_MANAGER.read_sum_lukoil(**param)
    df = pd.merge(df, df_lukoil, on=['Проект', 'Пользователь', 'Дата'], how='left')
    # df = df.replace([np.nan, -np.inf], 0)
    user = 'Тапехин Алексей Александрович'

    fte = param['fte']
    fact_sum = 'Фактические трудозатраты (час.) (Сумма)'
    headers = ['Дата', 'Проект', 'Пользователь', 'Лукойл, час.', 'Фактические трудозатраты (час.) (Сумма)', 'План, FTE',
               'Заявок лукойл']

    # fr = df[headers].loc[(df['Менеджер проекта'] == user) | (df['Пользователь'] == user)]

    fr = df.loc[(df['Менеджер проекта'] == user) | (df['Пользователь'] == user), headers]
    # fr_out = fr[fr['Лукойл, час.'].isna() == False]
    hours_plan = fte * fr['План, FTE']
    hours_plan_week = round(hours_plan / 4, 2)
    fr['План ч. мес.'] = round(hours_plan, 2)
    fr['План ч. нед.'] = hours_plan_week
    # f"{round(hours_plan, 2)}  / {round(hours_plan/4, 2)}"

    fact_fte = round((fr[fact_sum] / fte), 3)

    fr['Факт, FTE'] = fact_fte

    fr['Лукойл, FTE'] = fr['Лукойл, час.'].apply(lambda x: x / fte if x > 0 else 0)

    fr['DeltMes FTE'] = np.where(hours_plan > 0, fact_fte - fr['Лукойл, FTE'], 0)

    # Остаток часов
    fr['Остаток часов'] = np.where(hours_plan > 0, hours_plan - fr[fact_sum], 0)

    # Остаток FTE
    fr['Остаток FTE'] = fr.loc[(fr['Остаток часов'] > 0) & (fr['План ч. мес.'] > 0), 'Остаток часов'] / fte
    fr['Остаток FTE'] = fr['Остаток FTE'].fillna(0)


    # Суммирование по группам
    fr_grouped = fr.groupby(['Проект', 'Пользователь', 'План ч. мес.', 'План ч. нед.'], as_index=False).agg({
        'Заявок лукойл': 'sum',
        'Лукойл, час.': 'sum',
        'Фактические трудозатраты (час.) (Сумма)': 'sum',
        'План, FTE': 'sum',
        'Лукойл, FTE': 'sum',
        'Факт, FTE': 'sum',
        'DeltMes FTE': 'sum',
        'Остаток часов': 'sum',
        'Остаток FTE': 'sum',
    })

    fr = fr.reindex(
        columns=['Проект', 'Пользователь', 'План ч. мес.', 'План ч. нед.', 'Заявок лукойл', 'Лукойл, час.',
                 'Фактические трудозатраты (час.) (Сумма)',
                 'План, FTE', 'Лукойл, FTE', 'Факт, FTE', 'DeltMes FTE', 'Остаток часов', 'Остаток FTE'])

    columns_to_round = ['Лукойл, FTE', 'DeltMes FTE', 'Остаток часов', 'Остаток FTE']
    fr_grouped[columns_to_round] = fr_grouped[columns_to_round].round(3)

    # Замена 0 на пустую строку
    fr_grouped = fr_grouped.replace(0, '')

    # Замена NaN и сортировка
    fr_grouped = fr_grouped.fillna('').sort_values('Пользователь')

    # # Подготовка результата
    data = fr_grouped.to_records(index=False)

    columns = [{"name": col} for col in fr.columns]

    return {'columns': columns, 'data': data.tolist()}


def report2(**params):
    """
    Контроль заполнения факта за период

    """

    df = params['df']

    # Оптимизированная фильтрация с использованием .loc[]
    frm = df.loc[
        (df['ФИО'] == 'Тапехин Алексей Александрович') |
        (df['Проект'] == 'Т0133-КИС "Производственный учет и отчетность"'),
        ['Проект', 'ФИО', 'Дата', 'Трудозатрады за день']
    ]
    # fte = DB_MANAGER.get_middle_fte()
    fte = params['fte']
    date_range = pd.date_range(start=params['date_begin'], end=params['date_end'], freq='D')
    data_reg = frm[frm['Дата'].isin(date_range)]

    data_reg['Дата'] = pd.to_datetime(data_reg['Дата'], format='%d-%m-%Y').dt.strftime('%m-%Y')

    # Группировка данных по Проекту и ФИО, суммирование трудозатрат
    result = data_reg.groupby(['Дата', 'Проект', 'ФИО'], as_index=False).agg({'Трудозатрады за день': 'sum'})

    # Добавление столбца fte
    result['fte'] = round(result['Трудозатрады за день'] / int(fte), 3)

    # Сортировка по Дате и ФИО
    result = result.sort_values(by=['Дата', 'ФИО']).reset_index(drop=True)

    # Подготовка данных для отображения
    columns = [{"name": col, 'width':100} for col in result.columns]
    data = [tuple(row) for row in result.values]

    return {'columns': columns, 'data': data}


def get_data_report(**params):
    report_data = get_report(**params)
    reportnumber = report_data[0]

    params['df'] = report_data[1]
    params['date_begin'] = Univunit.convert_date(params['date_begin'])
    params['date_end'] = Univunit.convert_date(params['date_end'])

    report = REPORTS[reportnumber - 1]
    params['support'] = bool(report.get('support'))
    # Если ключа статус нет
    if report.get('status'):
        params['status'] = report.get('status', 'статус не указан')
    # if report.get('support'):
    #     params['support'] = bool(report.get('support', False))
    if report.get('headers'):
        params['headers'] = report.get('headers')
    if report.get('order by'):
        params['order by'] = report.get('order by')

    report_functions = {
        1: report1,
        2: report2,
        3: maintenance_sla,
        4: support_sla,
        5: report_lukoil,
    }

    frm = report_functions.get(reportnumber)
    # if frm is None:
    #     raise ValueError("Некорректный номер отчета")
    return frm(**params)


def get_report(**params):
    for items in REPORTS:
        if params['name_report'] == items['name']:
            result = (items['reportnumber'],
                      pd.read_excel(params['filename'], header=items['header_row'], parse_dates=items['data_columns'],
                                    date_format='%d.%m.%Y'))
            return result


def names_reports():
    return [items["name"] for items in REPORTS]


def report_lukoil(**params):
    # data_=("rec1", "rec2")

    df = params['df']
    # 'Исполнитель  по задаче', 'Трудозатраты по задаче (десят. часа)'
    # promeg = df.groupby(['Исполнитель  по задаче']).agg({'Трудозатраты по задаче (десят. часа)': 'sum'})
    # fr = df.groupby(['Исполнитель  по задаче']).agg({'Дата': 'max',  'Трудозатраты по задаче (десят. часа)': 'sum'})
    # columns = [{"name": "Код"}, {"name": "Дата"}]
    # data = df[params['headers']].to_records(index=False)
    # df[params['headers']].to_csv('data.csv', header=True, index=False, sep=';')

    # save_to_json(data=df[params['headers']], filename='my.json')

    # Добавляем столбец во фрэйм
    df['vid'] = np.where(df['Исполнитель  по задаче'] != 'Тапехин Алексей Александрович', "Поддержка", 'Сопровождение')

    # Копируем в отдельный фрейм данные
    kk = df.groupby(['vid', 'Исполнитель  по задаче']).agg(
        {
            'ID инцидента/ЗИ': "count",
            'Трудозатраты по задаче (десят. часа)': "sum",
        }
    ).copy()

    kk['sum_all'] = (kk['Трудозатраты по задаче (десят. часа)'].sum())
    kk['sum_vid'] = (kk.groupby("vid")['Трудозатраты по задаче (десят. часа)'].transform('sum'))
    kk['count_vid'] = (kk.groupby("vid")['Трудозатраты по задаче (десят. часа)'].transform('count'))

    kk['sum_ispol'] = (kk.groupby('Исполнитель  по задаче')['Трудозатраты по задаче (десят. часа)'].transform('sum'))
    # kk['count_vid'] = (kk.groupby('Исполнитель  по задаче')['Трудозатраты по задаче (десят. часа)'].transform('count'))
    data = kk.sort_values(["vid", 'Исполнитель  по задаче'])
    columns_ = data.columns.to_list()

    columns = [{"name": col} for col in columns_]

    return {'columns': columns, 'data': data.to_records(index=False)}


def get_data_lukoil(**param):
    # Определяем колонки для DataFrame
    data_fromsql = param['data_fromsql']

    col = ['Неделя', 'п/п', 'Заявка', 'Подзадача', 'Часы', 'Регистрация', 'Квартал', 'Месяц', 'Содержание']
    df = pd.DataFrame(data_fromsql, columns=col)
    # df.drop('Неделя', axis=1, inplace=True)
    # Преобразуем столбец с датами в datetime формат
    df['Регистрация'] = pd.to_datetime(df['Регистрация'], errors='coerce')  # Обработка ошибок преобразования

    # Проверка на наличие NaT после преобразования
    if df['Регистрация'].isnull().any():
        print("Некоторые даты были некорректными и будут проигнорированы.")
        df = df.dropna(subset=['Регистрация'])
    # fte = DB_MANAGER.get_middle_fte()
    fte = param['fte']
    # Добавляем столбец fte
    if not fte == '0':
        df['fte'] = round(df['Часы'] / int(fte), 3)

    df['Неделя'] = round(df['Неделя'], 0)
    # Находим начало месяца для каждой даты
    # df['month_start'] = df['Регистрация'].dt.to_period('M').dt.to_timestamp()

    # Рассчитываем, сколько недель прошло с начала месяца
    # df['Неделя'] = ((df['Регистрация'] - df['month_start']).dt.days // 7) + 1

    # Корректируем номер недели, чтобы он не превышал максимум
    # df['Неделя'] = df['Неделя'].clip(upper=5)

    # Группируем по номеру месяца и неделе, суммируем Часы и fte
    weekly_summary = df.groupby(['Месяц', 'Неделя'])[['Часы', 'fte']].sum().reset_index()

    # Устанавливаем новый индекс для отображения
    weekly_summary.set_index(['Месяц', 'Неделя'], inplace=True)

    # print("Группированные данные:\n", weekly_summary)  # Отладочный вывод
    weekly_summary['fte'] = weekly_summary['fte'].round(2)

    values = []
    for index, row in weekly_summary.iterrows():
        month_week = index
        values.append((month_week[0], month_week[1], row['Часы'], row['fte']))

    return values


def get_data_for_sla(**params):
    df = params["df"]
    # Фильтрация строк: исключаем строки со статусом "отмена"
    filtered_df = df[~df[status_column].astype(str).str.contains("Отменено", case=False, na=False)]

    # Фильтрация по датам (между начальной и конечной датой периода)
    df_dates = pd.to_datetime(filtered_df[date_column], errors='coerce').dropna()
    end_date = Univunit.convert_date(df_dates.max() + timedelta(days=1))

    date_begin = datetime.strptime(params['date_begin'], '%Y-%m-%d')
    date_end = datetime.strptime(end_date, '%Y-%m-%d')

    filtered_df[date_column] = pd.to_datetime(filtered_df[date_column], errors='coerce')
    date_filtered_df = filtered_df[(filtered_df[date_column] >= date_begin) & (filtered_df[date_column] <= date_end)]

    columns = [
        {"name": "№ п/п", "width": 100, "anchor": 'center'},
        {"name": "Наименование", "width": 600, "anchor": 'left'},
        {"name": "Значение", "width": 100, "anchor": 'center'}
    ]

    return (date_filtered_df, filtered_df, columns)


def support_sla(**params):
    """Линия пддержки расчет SLA"""
    # Проверка наличия столбцов

    inc_integr = 0
    fn = get_data_for_sla(**params)
    date_filtered_df = fn[0]
    filtered_df = fn[1]
    columns = fn[2]

    inc_data = filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False)
    idata = filtered_df[inc_data]

    # date_filtered_df = filtered_df[(filtered_df[date_column] >= date_begin) & (filtered_df[date_column] <= date_end)]
    inc_data_filtered = date_filtered_df[inc_data]

    # Суммирование значений по столбцам

    inc_registered_sum = idata[registered_column].sum()
    inc_complete_sum = idata[complete_period].sum()
    inc_complete_prosr_sum = idata[complete_prosr].sum()
    inc_open_end_prosr_sum = idata[open_end_prosr].sum()
    inc_open_begin_sum = idata[open_begin].sum()

    # Подсчет строк, содержащих "03. Changing" в столбце "rem_err_sla" для "INC"
    incorrect_count_esc = inc_data_filtered[rem_err_sla].astype(str).str.contains("02. incorrect", case=False,
                                                                                  na=False).sum()

    incorrect_count_cat = inc_data_filtered[rem_err_sla].astype(str).str.contains("03. Changing", case=False,
                                                                                  na=False).sum()

    inc_err_esk_sum = round(incorrect_count_esc / inc_data.count(), 2)
    inc_err_cat_sum = round(incorrect_count_cat / inc_data.count(), 2)

    # Затем применим операцию с нужным столбцом, уже без предупреждений о несоответствии индексов
    inc_reg_period_sum = pd.to_numeric(inc_data_filtered[inc_data][registered_column], errors='coerce').sum()

    # Дополнительный фильтр для "INC" с учетом столбца "Тип запроса" со значением "Инцидент"
    incident_data = filtered_df[(filtered_df[check_column].astype(str).str.contains("INC", case=False, na=False)) &
                                (filtered_df[request_type_column] == "Инцидент")]

    inc_incident_count = incident_data.shape[0]
    inc_incident_prosr_count = incident_data[incident_data["Просрочено в период"] == '1'].shape[0]
    # inc_open_end_prosr_sum = 0
    sla = round(
        (1 - (inc_complete_prosr_sum + inc_open_end_prosr_sum) / (inc_open_begin_sum + inc_reg_period_sum)) * 100,
        0)
    if sla >= 98:
        inc_integr = 1

    data = [
        (1, "Общее количество зарегистрированных заявок", inc_registered_sum),
        (2, "Общее количество выполненных заявок", inc_complete_sum),
        (3, "Общее количество зарегистрированных заявок за отчетный период, имеющих категорию «Инцидент»)",
         inc_incident_count),
        (4, "Количество заявок за период с превышением срока выполнения, имеющих категорию «Инцидент»",
         inc_incident_prosr_count),
        (5, "Количество заявок за период с превышением времени реакции по поддержке", 0),
        (6, "tur1 Количество закрытых заявок на поддержку с нарушением сроков заявок", inc_complete_prosr_sum),
        (7, "tur2 Количество незакрытых заявок, с нарушением срока", inc_open_end_prosr_sum),
        (8, "tur3 Количество перешедших с прошлого периода заявок на поддержку", inc_open_begin_sum),
        (9, "TUR4 Количество заявок, зарегистрированных в отчетном периоде", inc_reg_period_sum),
        (10, "EscM Доля ошибок эскалации", inc_err_esk_sum),
        (11, "CatM Доля ошибок категоризации", inc_err_cat_sum),
        (12, "Интегральный показатель качества оказания услуг по поддержке", inc_integr),
        (13, "Интегральный показатель качества оказания услуг по поддержке % ", sla),
    ]
    return {"columns": columns, 'data': data}


def maintenance_sla(**params):
    """Расчет SLA линии сопровождения"""

    crq_integr = 0
    fn = get_data_for_sla(**params)
    date_filtered_df = fn[0]
    filtered_df = fn[1]
    columns = fn[2]

    # Подсчет строк, содержащих "CRQ" в отфильтрованных данных
    crq_data = filtered_df[check_column].astype(str).str.contains("CRQ", case=False, na=False)
    crq_count = crq_data.sum()
    i_crq_data = filtered_df[crq_data]
    # Суммирование значений по столбцам

    crq_registered_sum = date_filtered_df[crq_data][registered_column].sum()
    crq_complete_sum = i_crq_data[complete_period].sum()
    crq_complete_prosr_sum = i_crq_data[complete_prosr].sum()
    crq_open_end_sum = i_crq_data[open_end].sum()
    crq_reactions_sum = i_crq_data[time_reactions].sum()
    crq_solved_sum = i_crq_data[time_solved].sum()
    crq_open_begin_sum = i_crq_data[open_begin].sum()

    if crq_complete_sum > 0:
        sla = round(100 * (crq_complete_sum - crq_complete_prosr_sum) / crq_complete_sum, 0)
    else:
        sla = 0

    if sla >= 98:
        crq_integr = 1

    print(f"Количество строк с 'CRQ' (без учета 'отмена'): {crq_count}")

    data = [
        (1, "1 tur3 Общее количество незакрытых заявок по сопровождению на начало периода", crq_open_begin_sum),
        (2, "tur4 Общее количество зарегистрированных заявок по сопровождению за отчетный период", crq_registered_sum),
        (3, "Общее количество закрытых за период заявок по сопровождению", crq_complete_sum),
        (
            4, "tur1 Общее количество закрытых за период заявок по сопровождению c нарушением SLA",
            crq_complete_prosr_sum),
        (5, "Общее количество незакрытых заявок по сопровождению на конец периода", crq_open_end_sum),
        (6, "tur2 Количество заявок за период с превышением времени реакции по сопровождению", crq_reactions_sum),
        (7, "Количество заявок за период с превышением срока выполнения по сопровождению", crq_solved_sum),
        (8, "Количество заявок за период с превышением времени диспетчеризации", 0),
        (9, "Уровень исполнения SLA", sla),
        (10, "  Интегральный показатель качества оказания услуг по сопровождению", crq_integr)
    ]
    return {"columns": columns, 'data': data}
