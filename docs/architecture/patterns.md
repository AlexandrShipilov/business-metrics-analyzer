# Паттерны проектирования Business Metrics Analyzer

## 1. Выбор паттернов

Паттерны подбирались по функциональным требованиям FR-01…FR-10 и нефункциональным требованиям из [business_requirements.md](../business_requirements.md) с учётом семи функциональных областей системы:

- аутентификация и управление пользователями;
- загрузка и импорт данных о продажах;
- расчёт KPI;
- визуализация и дашборды;
- формирование и экспорт отчётов;
- настройка метрик и плановых значений;
- логирование и аудит действий.

| Паттерн | Функциональная область | Требования | Где применяется | Обоснование | Альтернативы |
|---|---|---|---|---|---|
| Repository | Аутентификация и управление пользователями; загрузка и импорт данных; расчёт KPI; настройка метрик и плановых значений | FR-03, FR-05, FR-07, FR-08, FR-09 | Слой доступа к данным о продажах, посетителях, пользователях и плановых значениях KPI (`SqlSaleRepository`, `SqlUserRepository`, `SqlPlanRepository`) | Сервисы не зависят от SQL и SQLAlchemy. Фильтры по периоду, отделу, точке и менеджеру (FR-03) и ограничение данных по роли (FR-08) собраны в одном методе `get_by_filter`, а не разбросаны по коду. Репозиторий легко подменить заглушкой в тестах | Прямые запросы к ORM из сервисов и контроллеров |
| Unit of Work | Загрузка и импорт данных; аутентификация и управление пользователями; настройка метрик и плановых значений | FR-05, FR-07, FR-09 | Импорт данных о продажах из Excel, создание учётных записей и сохранение плановых значений в одной транзакции | Файл импорта записывается целиком или не записывается совсем: при ошибке в любой строке выполняется откат, и в базе не остаётся «половины» месяца (US-03). Один `commit` на всю операцию | Ручной вызов `commit` / `rollback` в каждом сервисе |
| Service Layer | Аутентификация и управление пользователями; загрузка и импорт данных; расчёт KPI; визуализация и дашборды; формирование и экспорт отчётов; настройка метрик и плановых значений | FR-01…FR-10 | Слой бизнес-сценариев: аутентификация, управление пользователями, импорт данных, расчёт KPI, формирование отчётов, настройка метрик (`AuthService`, `UserService`, `SalesImportService`, `KpiService`, `ReportService`, `MetricSettingsService`) | Бизнес-сценарии (загрузка, расчёт KPI, формирование отчёта) описаны в сервисах. Контроллеры FastAPI только принимают запрос и возвращают ответ. Один и тот же сценарий можно вызвать из API и из фоновой задачи | Логика в контроллерах FastAPI |
| Factory | Формирование и экспорт отчётов | FR-04, FR-06 | Создание отчётов разных типов: сводная таблица KPI, продажи по категориям, новые клиенты (`ReportFactory`) | Отчёт по FR-04 состоит из нескольких разделов разной структуры. Новый тип отчёта добавляется новым классом без правки `ReportService`. Так же позже добавляется экспорт в PDF рядом с Excel (FR-06) | Цепочка `if` / `elif` по типу отчёта |
| Strategy | Расчёт KPI; визуализация и дашборды; настройка метрик и плановых значений | FR-01, FR-02, FR-09 | Различные формулы расчёта KPI: выручка, средний чек, конверсия, рентабельность (раздел 1.2 требований) | Каждая формула – отдельный класс с одинаковым методом `calculate`. `KpiService` считает все карточки дашборда (FR-01) одним циклом. Новая метрика из настроек (FR-09) добавляется новой стратегией | Жёстко заданные функции расчёта внутри `KpiService` |
| DTO | Визуализация и дашборды; формирование и экспорт отчётов; аутентификация и управление пользователями | FR-01, FR-03, FR-04, FR-08, NFR-01 | Передача данных через REST API: карточки KPI и дашборд, отчёты, данные пользователей (`KpiCardDto`, `DashboardDto`, `ReportDto`, `UserDto`) | Чёткий контракт между API и интерфейсом. В DTO для менеджера и руководителя отдела не попадает рентабельность (FR-08), а в `UserDto` – хеш пароля. Передаются только нужные поля, что уменьшает ответ дашборда (NFR-01) | Отдача ORM-моделей или словарей напрямую |
| Adapter | Загрузка и импорт данных; формирование и экспорт отчётов | FR-05, FR-10, CN-03 | Интеграция с внешними источниками и сервисами: чтение файлов выгрузки из Excel и отправка писем через SMTP (`ExcelSalesSource`, `EmailNotifier`) | Сервис импорта работает с общим интерфейсом источника данных. Сейчас по CN-03 данные приходят только из Excel, позже добавляется `OneCSalesSource` без изменения сервиса. SMTP-библиотека скрыта за `EmailNotifier` | Прямые вызовы `pandas.read_excel` и `smtplib` в сервисах |
| Observer | Загрузка и импорт данных; расчёт KPI; визуализация и дашборды; логирование и аудит действий | FR-10, BR-06, NFR-01, NFR-03 | Реакция на загрузку новых данных: пересчёт кэша KPI для дашборда, проверка отклонения от плана, запись в журнал аудита | Импорт не знает о том, что происходит после него. По FR-10 при падении выручки или конверсии более чем на 10% от плана отправляется письмо; дашборд сразу получает пересчитанные KPI. Новый подписчик (например, аудит) добавляется без правки импорта | Прямые вызовы всех действий в `SalesImportService`; периодический опрос по расписанию |

## 2. Примеры кода

Ниже приведена упрощённая структура классов для трёх ключевых паттернов. Код показывает идею и будет дорабатываться при реализации.

### 2.1 Repository и Unit of Work

Репозиторий продаж выбирает чеки по фильтру. Ограничение по роли (FR-08) превращается в обычное условие фильтра: менеджер получает только свои чеки, руководитель – только свой отдел.

```python
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    department = Column(String)
    point = Column(String)
    manager = Column(String)
    category = Column(String)
    amount = Column(Float)
    cost = Column(Float)


class SaleFilter:
    def __init__(self, date_from, date_to, department=None, point=None, manager=None):
        self.date_from = date_from
        self.date_to = date_to
        self.department = department
        self.point = point
        self.manager = manager


def apply_role(user, sale_filter):
    # FR-08: менеджер видит свои данные, руководитель - свой отдел
    if user.role == "manager":
        sale_filter.manager = user.name
    elif user.role == "head":
        sale_filter.department = user.department
    return sale_filter


class SaleRepository:
    def add(self, sale):
        pass

    def get_by_filter(self, sale_filter):
        pass


class SqlSaleRepository(SaleRepository):
    def __init__(self, session):
        self.session = session

    def add(self, sale):
        self.session.add(sale)

    def get_by_filter(self, sale_filter):
        query = self.session.query(Sale)
        query = query.filter(Sale.date >= sale_filter.date_from)
        query = query.filter(Sale.date <= sale_filter.date_to)
        if sale_filter.department is not None:
            query = query.filter(Sale.department == sale_filter.department)
        if sale_filter.point is not None:
            query = query.filter(Sale.point == sale_filter.point)
        if sale_filter.manager is not None:
            query = query.filter(Sale.manager == sale_filter.manager)
        return query.all()


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.sales = SqlSaleRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()


class SalesImportService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def import_rows(self, rows):
        # если в любой строке ошибка, весь файл откатывается
        with UnitOfWork(self.session_factory) as uow:
            for row in rows:
                if row["amount"] < 0:
                    raise ValueError("Отрицательная сумма чека")
                uow.sales.add(Sale(**row))
        return len(rows)
```

### 2.2 Strategy для расчёта KPI

Все стратегии получают одни и те же исходные данные `KpiData`, поэтому их можно менять местами и перебирать в цикле. Формулы взяты из раздела 1.2 требований.

```python
class KpiData:
    def __init__(self, revenue, cost, checks, visitors):
        self.revenue = revenue
        self.cost = cost
        self.checks = checks
        self.visitors = visitors


class KpiStrategy:
    name = ""

    def calculate(self, data):
        pass


class RevenueStrategy(KpiStrategy):
    name = "Выручка"

    def calculate(self, data):
        return data.revenue


class AverageCheckStrategy(KpiStrategy):
    name = "Средний чек"

    def calculate(self, data):
        if data.checks == 0:
            return 0.0
        return data.revenue / data.checks


class ConversionStrategy(KpiStrategy):
    name = "Конверсия, %"

    def calculate(self, data):
        if data.visitors == 0:
            return 0.0
        return data.checks / data.visitors * 100


class ProfitabilityStrategy(KpiStrategy):
    name = "Рентабельность, %"

    def calculate(self, data):
        if data.revenue == 0:
            return 0.0
        return (data.revenue - data.cost) / data.revenue * 100


class KpiService:
    def __init__(self, strategies):
        self.strategies = strategies

    def calculate_all(self, data):
        result = {}
        for strategy in self.strategies:
            result[strategy.name] = round(strategy.calculate(data), 2)
        return result


# для менеджера и руководителя отдела рентабельность не передаётся (FR-08)
director_kpi = KpiService([RevenueStrategy(), AverageCheckStrategy(),
                           ConversionStrategy(), ProfitabilityStrategy()])
manager_kpi = KpiService([RevenueStrategy(), AverageCheckStrategy(),
                          ConversionStrategy()])
```

### 2.3 Observer для реакции на загрузку данных

После импорта публикуется событие `data_imported`. Подписчики не знают друг о друге: один пересчитывает KPI для дашборда, другой проверяет план (FR-10), третий пишет журнал аудита.

```python
class EventBus:
    def __init__(self):
        self.handlers = {}

    def subscribe(self, event_name, handler):
        if event_name not in self.handlers:
            self.handlers[event_name] = []
        self.handlers[event_name].append(handler)

    def publish(self, event_name, data):
        for handler in self.handlers.get(event_name, []):
            handler(data)


class DeviationChecker:
    def __init__(self, notifier):
        self.notifier = notifier

    def __call__(self, data):
        # FR-10: факт ниже плана более чем на 10%
        if data["revenue"] < data["revenue_plan"] * 0.9:
            self.notifier.send("director@company.ru",
                               "Выручка ниже плана более чем на 10%")


class AuditLogger:
    def __call__(self, data):
        print("Аудит: загружен файл", data["file_name"], "пользователем", data["user"])


def refresh_kpi_cache(data):
    print("Пересчёт KPI за период", data["period"])


bus = EventBus()
bus.subscribe("data_imported", refresh_kpi_cache)
bus.subscribe("data_imported", AuditLogger())
# notifier - это EmailNotifier (Adapter над SMTP)
# bus.subscribe("data_imported", DeviationChecker(notifier))
```
