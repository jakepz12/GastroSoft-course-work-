# GastroSoft course work

Desktop-прототип ресторанной системы на Python и PySide6.

## Запуск

1. Убедись, что установлен Python 3.14+.
2. Установи зависимости: `python -m pip install -r requirements.txt`
3. Запусти приложение: `python run_gastrosoft.py`

## Подключение MySQL

В проекте есть отдельный файл подключения: [mysql_connection.py](C:/Users/ilari/source/repos/jakepz12/GastroSoft-course-work-/mysql_connection.py)

Что сделать:

1. Скопируй [mysql_config.example.json](C:/Users/ilari/source/repos/jakepz12/GastroSoft-course-work-/mysql_config.example.json) в `mysql_config.json`.
2. Заполни в `mysql_config.json` свои параметры `host`, `port`, `user`, `password`, `database`.
3. Для проверки соединения выполни: `python mysql_connection.py`
4. Для создания схемы из уже существующего SQL-файла выполни: `python mysql_connection.py --init`
5. Для отдельной проверки доступа к базе после инициализации выполни: `python mysql_connection.py --test-db`

Файл [mysql_connection.py](C:/Users/ilari/source/repos/jakepz12/GastroSoft-course-work-/mysql_connection.py) использует уже существующий [gastrosoft_mysql.sql](C:/Users/ilari/source/repos/jakepz12/GastroSoft-course-work-/gastrosoft_mysql.sql), поэтому структура базы поднимается из твоего SQL-скрипта, а не дублируется заново в коде.

После появления `mysql_config.json` приложение при запуске автоматически попробует подключиться к MySQL через [gastrosoft_app/mysql_store.py](C:/Users/ilari/source/repos/jakepz12/GastroSoft-course-work-/gastrosoft_app/mysql_store.py). Если база доступна и схема применена, интерфейс загрузит роли, сотрудников, столы, брони, меню, заказы и склад из MySQL. Если MySQL недоступен или схема ещё не создана, приложение продолжит работать на демо-данных.

## Демо-аккаунты

- `director / 1234`
- `chef / 1234`
- `cook / 1234`
- `waiter / 1234`
- `cashier / 1234`

## Доступ по ролям

- `Администратор системы`, `Директор` — все разделы.
- `Менеджер зала` — бронирования и оформление заказов.
- `Официант` — только оформление заказа и передача на кухню.
- `Кассир` — только закрытие готовых заказов.
- `Шеф-повар`, `Повар` — только кухонная очередь и статусы приготовления.
- `Бухгалтер` — только склад и отчеты.

Для оформления заказа в базе должны быть заполнены справочники столов, категорий меню и блюд. Если они пустые, выпадающие списки будут заблокированы, а интерфейс покажет причину.

## Что есть в приложении

- отдельная страница авторизации и регистрации;
- главный экран с KPI, графиком продаж и быстрыми переходами;
- экран смен и персонала;
- экран бронирований и столов;
- экран заказов и кухни;
- экран склада и отчетности.

## Структура

- `run_gastrosoft.py` — точка входа.
- `gastrosoft_app/shell.py` — оболочка приложения и навигация.
- `gastrosoft_app/pages/*.py` — отдельные страницы.
- `gastrosoft_app/styles/*/style.css` — отдельные CSS-файлы для каждой страницы и оболочки.
- `gastrosoft_app/data.py` — демо-данные и рабочая логика кнопок.
