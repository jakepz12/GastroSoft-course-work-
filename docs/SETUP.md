# Инструкция подключения GastroSoft

## Требования

- Python 3.14+
- MySQL 8.0+ или MariaDB 10.5+
- pip (менеджер пакетов Python)

---

## Быстрый старт (без MySQL)

Если MySQL не нужен, приложение запускается сразу:

```bash
# 1. Установи зависимости
python -m pip install -r requirements.txt

# 2. Запусти приложение
python run_gastrosoft.py
```

Приложение запустится в демо-режиме с пустыми данными. Все функции будут доступны, но данные не сохраняются.

---

## Подключение к MySQL

### Шаг 1: Установи MySQL

**macOS (Homebrew):**
```bash
brew install mysql
brew services start mysql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

**Windows:**
Скачай MySQL Installer с https://dev.mysql.com/downloads/installer/

### Шаг 2: Настрой конфигурацию

Скопируй файл конфигурации:
```bash
cp mysql_config.example.json mysql_config.json
```

Отредактируй `mysql_config.json`:
```json
{
  "host": "127.0.0.1",
  "port": 3307,
  "user": "root",
  "password": "твой_пароль",
  "database": "gastrosoft_course",
  "charset": "utf8mb4"
}
```

**Важно:**
- Порт по умолчанию: **3307** (не 3306!)
- Если MySQL установлен через Docker, порт может быть другим
- Убедись, что пользователь `root` имеет права на создание баз данных

### Шаг 3: Создай базу данных и схему

```bash
python mysql_connection.py --init
```

Эта команда:
1. Подключается к MySQL
2. Создаёт базу данных `gastrosoft_course`
3. Применяет схему из `gastrosoft_mysql.sql`
4. Создаёт все таблицы и индексы

### Шаг 4: Заполни тестовыми данными

```bash
python sql/seed_meaningful_data.py
```

Эта команда заполнит базу:
- Ролями сотрудников
- Сотрудниками (директор, шеф-повар, повара, официант, бухгалтер)
- Учётными записями для входа
- Столами ресторана
- Меню (Закуски, Супы, Горячее, Напитки)
- Ингредиентами и складскими операциями
- Бронированиями
- Заказами в разных статусах

### Шаг 5: Проверь подключение

```bash
# Проверка соединения с MySQL
python mysql_connection.py

# Проверка доступа к базе данных
python mysql_connection.py --test-db
```

### Шаг 6: Запусти приложение

```bash
python run_gastrosoft.py
```

В статусе внизу должно отображаться: `База данных доступна: gastrosoft_course`

---

## Демо-аккаунты

| Логин | Пароль | Роль |
|-------|--------|------|
| director | 1234 | Директор |
| chef | 1234 | Шеф-повар |
| cook | 1234 | Повар |
| waiter | 1234 | Официант |

---

## Доступ по ролям

| Роль | Страницы | Возможности |
|------|----------|-------------|
| Директор | Все | Полный доступ ко всем функциям |
| Шеф-повар | Кухня, Заказы, Отчёты | Управление очередью, назначение поваров, приоритеты, статистика |
| Повар | Кухня | Приготовление заказов, отметка готовности |
| Официант | Заказы | Создание заказов, примечания, закрытие выданных |
| Менеджер зала | Бронирования, Заказы | Управление посадкой гостей |
| Бухгалтер | Склад | Складские операции и отчёты |

---

## Структура проекта

```
GastroSoft-course-work--main/
├── run_gastrosoft.py              # Точка входа
├── gastrosoft_mysql.sql           # SQL-схема базы данных
├── mysql_connection.py            # Менеджер подключения к MySQL
├── mysql_config.json              # Конфигурация подключения (не коммитить!)
├── mysql_config.example.json      # Пример конфигурации
├── requirements.txt               # Зависимости
├── gastrosoft_app/
│   ├── app.py                     # Инициализация QApplication
│   ├── shell.py                   # Главное окно и навигация
│   ├── mysql_store.py             # Слой данных (вся логика БД)
│   ├── data.py                    # DemoStore — заглушка без MySQL
│   ├── role_access.py             # RBAC: доступ ролей
│   ├── widgets.py                 # Переиспользуемые виджеты
│   ├── style_utils.py             # Загрузка QSS-стилей
│   ├── pages/
│   │   ├── auth_page.py           # Авторизация
│   │   ├── dashboard_page.py      # Главная панель
│   │   ├── orders_page.py         # Заказы (официант)
│   │   ├── kitchen_page.py        # Кухня (шеф/повар)
│   │   ├── reports_page.py        # Отчёты (шеф-повар)
│   │   ├── reservations_page.py   # Бронирования
│   │   ├── staff_page.py          # Смены
│   │   └── inventory_page.py      # Склад
│   └── styles/                    # QSS-стили для каждой страницы
└── sql/
    └── seed_meaningful_data.py    # Заполнение БД тестовыми данными
```

---

## Решение проблем

### Ошибка: "Файл конфигурации не найден"
Убедись, что файл `mysql_config.json` существует в корне проекта.

### Ошибка: "Access denied for user 'root'"
Проверь пароль в `mysql_config.json`. Убедись, что пользователь имеет права на БД.

### Ошибка: "Can't connect to MySQL server"
- Проверь, что MySQL запущен
- Проверь порт (по умолчанию 3307, не 3306)
- Проверь, что MySQL слушает на `127.0.0.1`

### Ошибка: "Unknown database 'gastrosoft_course'"
Запусти инициализацию: `python mysql_connection.py --init`

### Приложение запускается с пустыми данными
Это нормально — MySQL не подключен. Проверь `mysql_config.json` и запусти `python mysql_connection.py --test-db`.

### Ошибки при заполнении тестовыми данными
Если база уже заполнена, сначала переинициализируй:
```bash
python mysql_connection.py --init
python sql/seed_meaningful_data.py
```

---

## Полезные команды

```bash
# Проверка соединения
python mysql_connection.py

# Инициализация схемы
python mysql_connection.py --init

# Проверка доступа к базе
python mysql_connection.py --test-db

# Заполнение тестовыми данными
python sql/seed_meaningful_data.py

# Запуск приложения
python run_gastrosoft.py
```
