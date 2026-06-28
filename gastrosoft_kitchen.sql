-- ============================================================
-- GastroSoft — Схема БД кухонного модуля
-- Роли: Официант, Повар, Шеф-повар
-- ============================================================

DROP DATABASE IF EXISTS gastrosoft_kitchen;
CREATE DATABASE gastrosoft_kitchen
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE gastrosoft_kitchen;


-- ============================================================
-- СПРАВОЧНИКИ
-- ============================================================

CREATE TABLE employee_role (
  role_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_role_code (code),
  UNIQUE KEY uq_role_name (name)
) ENGINE=InnoDB;

CREATE TABLE measurement_unit (
  measurement_unit_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  name VARCHAR(50) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (measurement_unit_id),
  UNIQUE KEY uq_measurement_unit_code (code),
  UNIQUE KEY uq_measurement_unit_name (name)
) ENGINE=InnoDB;

CREATE TABLE order_status (
  order_status_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (order_status_id),
  UNIQUE KEY uq_order_status_code (code),
  UNIQUE KEY uq_order_status_name (name)
) ENGINE=InnoDB;

CREATE TABLE order_item_status (
  order_item_status_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (order_item_status_id),
  UNIQUE KEY uq_order_item_status_code (code),
  UNIQUE KEY uq_order_item_status_name (name)
) ENGINE=InnoDB;

CREATE TABLE payment_method (
  payment_method_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (payment_method_id),
  UNIQUE KEY uq_payment_method_code (code),
  UNIQUE KEY uq_payment_method_name (name)
) ENGINE=InnoDB;

CREATE TABLE stock_operation_type (
  stock_operation_type_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  operation_sign SMALLINT NOT NULL,
  PRIMARY KEY (stock_operation_type_id),
  UNIQUE KEY uq_stock_operation_type_code (code),
  UNIQUE KEY uq_stock_operation_type_name (name)
) ENGINE=InnoDB;


-- ============================================================
-- ПЕРСОНАЛ И ДОСТУП
-- ============================================================

CREATE TABLE employee (
  employee_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_id INT UNSIGNED NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100) DEFAULT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  email VARCHAR(100) DEFAULT NULL,
  hire_date DATE DEFAULT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (employee_id),
  KEY idx_employee_role (role_id),
  KEY idx_employee_name (last_name, first_name),
  CONSTRAINT fk_employee_role
    FOREIGN KEY (role_id) REFERENCES employee_role (role_id)
) ENGINE=InnoDB;

CREATE TABLE app_user (
  user_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  employee_id INT UNSIGNED NOT NULL,
  login VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_app_user_employee (employee_id),
  UNIQUE KEY uq_app_user_login (login),
  CONSTRAINT fk_app_user_employee
    FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
) ENGINE=InnoDB;


-- ============================================================
-- ЗАЛ И СТОЛЫ
-- ============================================================

CREATE TABLE restaurant_table (
  table_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  seats_count TINYINT UNSIGNED NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (table_id),
  UNIQUE KEY uq_restaurant_table_code (code)
) ENGINE=InnoDB;


-- ============================================================
-- МЕНЮ И ПРОИЗВОДСТВО
-- ============================================================

CREATE TABLE menu_category (
  category_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  PRIMARY KEY (category_id),
  UNIQUE KEY uq_menu_category_name (name)
) ENGINE=InnoDB;

CREATE TABLE dish (
  dish_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT DEFAULT NULL,
  base_price DECIMAL(10,2) NOT NULL,
  prep_time_minutes INT UNSIGNED DEFAULT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  photo_url VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (dish_id),
  UNIQUE KEY uq_dish_name (name),
  KEY idx_dish_category (category_id),
  CONSTRAINT fk_dish_category
    FOREIGN KEY (category_id) REFERENCES menu_category (category_id)
) ENGINE=InnoDB;

CREATE TABLE modifier_group (
  modifier_group_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (modifier_group_id),
  UNIQUE KEY uq_modifier_group_name (name)
) ENGINE=InnoDB;

CREATE TABLE dish_modifier_group (
  dish_id INT UNSIGNED NOT NULL,
  modifier_group_id INT UNSIGNED NOT NULL,
  min_select_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
  max_select_count TINYINT UNSIGNED NOT NULL DEFAULT 1,
  sort_order INT NOT NULL DEFAULT 0,
  PRIMARY KEY (dish_id, modifier_group_id),
  KEY idx_dish_modifier_group_group (modifier_group_id),
  CONSTRAINT fk_dish_modifier_group_dish
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id) ON DELETE CASCADE,
  CONSTRAINT fk_dish_modifier_group_group
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_group (modifier_group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE modifier_option (
  modifier_option_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  modifier_group_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  extra_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (modifier_option_id),
  UNIQUE KEY uq_modifier_option_group_name (modifier_group_id, name),
  CONSTRAINT fk_modifier_option_group
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_group (modifier_group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ingredient (
  ingredient_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  measurement_unit_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  cost_per_unit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  critical_level DECIMAL(10,3) NOT NULL DEFAULT 0.000,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (ingredient_id),
  UNIQUE KEY uq_ingredient_name (name),
  KEY idx_ingredient_unit (measurement_unit_id),
  CONSTRAINT fk_ingredient_unit
    FOREIGN KEY (measurement_unit_id) REFERENCES measurement_unit (measurement_unit_id)
) ENGINE=InnoDB;

CREATE TABLE recipe_item (
  dish_id INT UNSIGNED NOT NULL,
  ingredient_id INT UNSIGNED NOT NULL,
  quantity DECIMAL(10,3) NOT NULL,
  PRIMARY KEY (dish_id, ingredient_id),
  KEY idx_recipe_item_ingredient (ingredient_id),
  CONSTRAINT fk_recipe_item_dish
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id) ON DELETE CASCADE,
  CONSTRAINT fk_recipe_item_ingredient
    FOREIGN KEY (ingredient_id) REFERENCES ingredient (ingredient_id)
) ENGINE=InnoDB;


-- ============================================================
-- ЗАКАЗЫ
-- ============================================================

CREATE TABLE customer_order (
  order_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  table_id INT UNSIGNED DEFAULT NULL,
  order_status_id INT UNSIGNED NOT NULL,
  created_by_user_id INT UNSIGNED NOT NULL,
  assigned_cook_id INT UNSIGNED DEFAULT NULL,
  priority ENUM('normal','rush') NOT NULL DEFAULT 'normal',
  payment_method_id INT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME DEFAULT NULL,
  closed_at DATETIME DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (order_id),
  KEY idx_customer_order_table (table_id),
  KEY idx_customer_order_status (order_status_id),
  KEY idx_customer_order_created_by (created_by_user_id),
  KEY idx_customer_order_cook (assigned_cook_id),
  KEY idx_customer_order_payment_method (payment_method_id),
  KEY idx_customer_order_created_at (created_at),
  CONSTRAINT fk_customer_order_table
    FOREIGN KEY (table_id) REFERENCES restaurant_table (table_id),
  CONSTRAINT fk_customer_order_status
    FOREIGN KEY (order_status_id) REFERENCES order_status (order_status_id),
  CONSTRAINT fk_customer_order_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES app_user (user_id),
  CONSTRAINT fk_customer_order_cook
    FOREIGN KEY (assigned_cook_id) REFERENCES employee (employee_id),
  CONSTRAINT fk_customer_order_payment_method
    FOREIGN KEY (payment_method_id) REFERENCES payment_method (payment_method_id)
) ENGINE=InnoDB;

CREATE TABLE order_item (
  order_item_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id INT UNSIGNED NOT NULL,
  dish_id INT UNSIGNED NOT NULL,
  order_item_status_id INT UNSIGNED NOT NULL,
  quantity INT UNSIGNED NOT NULL DEFAULT 1,
  unit_price DECIMAL(10,2) NOT NULL,
  assigned_cook_id INT UNSIGNED DEFAULT NULL,
  started_at DATETIME DEFAULT NULL,
  ready_at DATETIME DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (order_item_id),
  KEY idx_order_item_order (order_id),
  KEY idx_order_item_dish (dish_id),
  KEY idx_order_item_status (order_item_status_id),
  KEY idx_order_item_cook (assigned_cook_id),
  CONSTRAINT fk_order_item_order
    FOREIGN KEY (order_id) REFERENCES customer_order (order_id) ON DELETE CASCADE,
  CONSTRAINT fk_order_item_dish
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id),
  CONSTRAINT fk_order_item_status
    FOREIGN KEY (order_item_status_id) REFERENCES order_item_status (order_item_status_id),
  CONSTRAINT fk_order_item_cook
    FOREIGN KEY (assigned_cook_id) REFERENCES employee (employee_id)
) ENGINE=InnoDB;

CREATE TABLE order_item_modifier (
  order_item_id INT UNSIGNED NOT NULL,
  modifier_option_id INT UNSIGNED NOT NULL,
  extra_charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (order_item_id, modifier_option_id),
  KEY idx_order_item_modifier_option (modifier_option_id),
  CONSTRAINT fk_order_item_modifier_order_item
    FOREIGN KEY (order_item_id) REFERENCES order_item (order_item_id) ON DELETE CASCADE,
  CONSTRAINT fk_order_item_modifier_option
    FOREIGN KEY (modifier_option_id) REFERENCES modifier_option (modifier_option_id)
) ENGINE=InnoDB;


-- ============================================================
-- СКЛАД И КУХОННЫЙ ЖУРНАЛ
-- ============================================================

CREATE TABLE inventory_operation (
  operation_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ingredient_id INT UNSIGNED NOT NULL,
  stock_operation_type_id INT UNSIGNED NOT NULL,
  quantity DECIMAL(10,3) NOT NULL,
  operation_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  performed_by_user_id INT UNSIGNED DEFAULT NULL,
  related_order_item_id INT UNSIGNED DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (operation_id),
  KEY idx_inventory_operation_ingredient (ingredient_id),
  KEY idx_inventory_operation_type (stock_operation_type_id),
  KEY idx_inventory_operation_datetime (operation_datetime),
  KEY idx_inventory_operation_user (performed_by_user_id),
  KEY idx_inventory_operation_order_item (related_order_item_id),
  CONSTRAINT fk_inventory_operation_ingredient
    FOREIGN KEY (ingredient_id) REFERENCES ingredient (ingredient_id),
  CONSTRAINT fk_inventory_operation_type
    FOREIGN KEY (stock_operation_type_id) REFERENCES stock_operation_type (stock_operation_type_id),
  CONSTRAINT fk_inventory_operation_user
    FOREIGN KEY (performed_by_user_id) REFERENCES app_user (user_id),
  CONSTRAINT fk_inventory_operation_order_item
    FOREIGN KEY (related_order_item_id) REFERENCES order_item (order_item_id)
) ENGINE=InnoDB;

CREATE TABLE kitchen_log (
  log_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id INT UNSIGNED NOT NULL,
  order_item_id INT UNSIGNED DEFAULT NULL,
  action VARCHAR(50) NOT NULL,
  performed_by_user_id INT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (log_id),
  KEY idx_kitchen_log_order (order_id),
  KEY idx_kitchen_log_item (order_item_id),
  KEY idx_kitchen_log_created (created_at),
  CONSTRAINT fk_kitchen_log_order
    FOREIGN KEY (order_id) REFERENCES customer_order (order_id),
  CONSTRAINT fk_kitchen_log_item
    FOREIGN KEY (order_item_id) REFERENCES order_item (order_item_id),
  CONSTRAINT fk_kitchen_log_user
    FOREIGN KEY (performed_by_user_id) REFERENCES app_user (user_id)
) ENGINE=InnoDB;


-- ============================================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================================

CREATE OR REPLACE VIEW v_order_total AS
SELECT
  oi.order_id,
  SUM(oi.quantity * (oi.unit_price + COALESCE(mods.modifier_total_per_unit, 0.00))) AS total_amount
FROM order_item oi
LEFT JOIN (
  SELECT
    order_item_id,
    SUM(extra_charge) AS modifier_total_per_unit
  FROM order_item_modifier
  GROUP BY order_item_id
) mods ON mods.order_item_id = oi.order_item_id
GROUP BY oi.order_id;

CREATE OR REPLACE VIEW v_ingredient_stock_balance AS
SELECT
  io.ingredient_id,
  SUM(io.quantity * sot.operation_sign) AS current_quantity
FROM inventory_operation io
JOIN stock_operation_type sot
  ON sot.stock_operation_type_id = io.stock_operation_type_id
GROUP BY io.ingredient_id;


-- ============================================================
-- НАПОЛНЕНИЕ СПРАВОЧНИКОВ
-- ============================================================

INSERT INTO employee_role (code, name, description) VALUES
  ('CHEF', 'Шеф-повар', 'Управление операциями кухни'),
  ('COOK', 'Повар', 'Приготовление блюд'),
  ('WAITER', 'Официант', 'Обслуживание гостей и приём заказов');

INSERT INTO measurement_unit (code, name, description) VALUES
  ('g', 'Грамм', 'Вес в граммах'),
  ('kg', 'Килограмм', 'Вес в килограммах'),
  ('ml', 'Миллилитр', 'Объём в миллилитрах'),
  ('l', 'Литр', 'Объём в литрах'),
  ('pcs', 'Штука', 'Штучная единица');

INSERT INTO order_status (code, name) VALUES
  ('NEW', 'Новый'),
  ('ACCEPTED', 'Принят'),
  ('PREPARING', 'Готовится'),
  ('READY', 'Готов'),
  ('SERVED', 'Выдан'),
  ('CLOSED', 'Закрыт'),
  ('CANCELLED', 'Отменён');

INSERT INTO order_item_status (code, name) VALUES
  ('QUEUED', 'В очереди'),
  ('COOKING', 'Готовится'),
  ('READY', 'Готово'),
  ('SERVED', 'Подано'),
  ('CANCELLED', 'Отменено');

INSERT INTO payment_method (code, name) VALUES
  ('CASH', 'Наличные'),
  ('CARD', 'Карта'),
  ('ONLINE', 'Онлайн');

INSERT INTO stock_operation_type (code, name, operation_sign) VALUES
  ('RECEIPT', 'Поступление', 1),
  ('WRITE_OFF', 'Списание', -1),
  ('ADJUSTMENT_IN', 'Корректировка+', 1),
  ('ADJUSTMENT_OUT', 'Корректировка-', -1);


-- ============================================================
-- ТЕСТОВЫЕ ДАННЫЕ
-- ============================================================

-- Сотрудники
INSERT INTO employee (role_id, last_name, first_name, middle_name, phone, email, hire_date, is_active) VALUES
  ((SELECT role_id FROM employee_role WHERE code = 'CHEF'), 'Волков', 'Илья', NULL, '+7 900 100-10-02', 'chef@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'WAITER'), 'Белова', 'Мария', NULL, '+7 900 100-10-03', 'waiter@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'COOK'), 'Громов', 'Павел', NULL, '+7 900 100-10-06', 'cook1@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'COOK'), 'Котов', 'Даниил', NULL, '+7 900 100-10-07', 'cook2@gastrosoft.local', CURRENT_DATE(), 1);

-- Учётные записи
INSERT INTO app_user (employee_id, login, password_hash, is_active) VALUES
  ((SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'), 'chef', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'cook1@gastrosoft.local'), 'cook', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'waiter@gastrosoft.local'), 'waiter', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1);

-- Столы
INSERT INTO restaurant_table (code, seats_count, is_active, note) VALUES
  ('T-01', 2, 1, 'У окна'),
  ('T-02', 2, 1, 'У бара'),
  ('T-03', 4, 1, 'Главный зал'),
  ('T-04', 4, 1, 'Главный зал'),
  ('T-05', 6, 1, 'Семейный стол'),
  ('T-06', 6, 1, 'VIP-зона');

-- Меню
INSERT INTO menu_category (name, description, sort_order) VALUES
  ('Закуски', 'Закуски и стартеры', 10),
  ('Супы', 'Супы', 20),
  ('Горячее', 'Основные блюда', 30),
  ('Напитки', 'Напитки', 40);

INSERT INTO dish (category_id, name, description, base_price, prep_time_minutes, is_active) VALUES
  ((SELECT category_id FROM menu_category WHERE name = 'Закуски'), 'Брускетта с томатами', 'Хрустящий хлеб с томатами и базиликом', 390.00, 7, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Закуски'), 'Тар-тар из лосося', 'Лосось с соусом и зеленью', 540.00, 10, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Супы'), 'Том Ям', 'Острый суп с морепродуктами', 620.00, 12, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Супы'), 'Крем-суп из грибов', 'Грибной крем-суп со сливками', 430.00, 9, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Горячее'), 'Паста Альфредо', 'Паста со сливочным соусом', 590.00, 15, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Горячее'), 'Бургер GastroSoft', 'Фирменный бургер с котлетой', 670.00, 14, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Напитки'), 'Лимонад базилик-лайм', 'Домашний лимонад', 260.00, 3, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Напитки'), 'Эспрессо', 'Классический кофе', 170.00, 2, 1);

-- Модификаторы
INSERT INTO modifier_group (name, description) VALUES
  ('Острота', 'Уровень остроты блюда'),
  ('Исключить ингредиент', 'Убрать нежелательный ингредиент');

INSERT INTO modifier_option (modifier_group_id, name, extra_price, is_active) VALUES
  ((SELECT modifier_group_id FROM modifier_group WHERE name = 'Острота'), 'Не остро', 0.00, 1),
  ((SELECT modifier_group_id FROM modifier_group WHERE name = 'Острота'), 'Средне остро', 0.00, 1),
  ((SELECT modifier_group_id FROM modifier_group WHERE name = 'Острота'), 'Очень остро', 50.00, 1),
  ((SELECT modifier_group_id FROM modifier_group WHERE name = 'Исключить ингредиент'), 'Без лука', 0.00, 1),
  ((SELECT modifier_group_id FROM modifier_group WHERE name = 'Исключить ингредиент'), 'Без зелени', 0.00, 1);

INSERT INTO dish_modifier_group (dish_id, modifier_group_id, min_select_count, max_select_count, sort_order) VALUES
  ((SELECT dish_id FROM dish WHERE name = 'Том Ям'), (SELECT modifier_group_id FROM modifier_group WHERE name = 'Острота'), 0, 1, 0),
  ((SELECT dish_id FROM dish WHERE name = 'Бургер GastroSoft'), (SELECT modifier_group_id FROM modifier_group WHERE name = 'Исключить ингредиент'), 0, 1, 0);

-- Ингредиенты и рецептура
INSERT INTO ingredient (measurement_unit_id, name, cost_per_unit, critical_level, is_active) VALUES
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Томаты', 180.00, 5.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'l'), 'Сливки', 220.00, 3.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Лосось', 1300.00, 2.500, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'pcs'), 'Булочки бриошь', 45.00, 10.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Кофе зерно', 900.00, 1.500, 1);

INSERT INTO recipe_item (dish_id, ingredient_id, quantity) VALUES
  ((SELECT dish_id FROM dish WHERE name = 'Бургер GastroSoft'), (SELECT ingredient_id FROM ingredient WHERE name = 'Булочки бриошь'), 0.200),
  ((SELECT dish_id FROM dish WHERE name = 'Бургер GastroSoft'), (SELECT ingredient_id FROM ingredient WHERE name = 'Томаты'), 0.050),
  ((SELECT dish_id FROM dish WHERE name = 'Том Ям'), (SELECT ingredient_id FROM ingredient WHERE name = 'Сливки'), 0.150),
  ((SELECT dish_id FROM dish WHERE name = 'Том Ям'), (SELECT ingredient_id FROM ingredient WHERE name = 'Томаты'), 0.100);

-- Начальные остатки
INSERT INTO inventory_operation (ingredient_id, stock_operation_type_id, quantity, performed_by_user_id, note) VALUES
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Томаты'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 4.600, (SELECT user_id FROM app_user WHERE login = 'chef'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Сливки'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 7.500, (SELECT user_id FROM app_user WHERE login = 'chef'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Лосось'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 3.100, (SELECT user_id FROM app_user WHERE login = 'chef'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Булочки бриошь'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 14.000, (SELECT user_id FROM app_user WHERE login = 'chef'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Кофе зерно'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 2.200, (SELECT user_id FROM app_user WHERE login = 'chef'), 'Начальный остаток');

-- Тестовые заказы
INSERT INTO customer_order (table_id, order_status_id, created_by_user_id, assigned_cook_id, priority, payment_method_id, created_at, started_at) VALUES
  ((SELECT table_id FROM restaurant_table WHERE code = 'T-03'), (SELECT order_status_id FROM order_status WHERE code = 'PREPARING'), (SELECT user_id FROM app_user WHERE login = 'waiter'), (SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'), 'normal', (SELECT payment_method_id FROM payment_method WHERE code = 'CARD'), DATE_SUB(NOW(), INTERVAL 20 MINUTE), DATE_SUB(NOW(), INTERVAL 18 MINUTE)),
  ((SELECT table_id FROM restaurant_table WHERE code = 'T-01'), (SELECT order_status_id FROM order_status WHERE code = 'ACCEPTED'), (SELECT user_id FROM app_user WHERE login = 'waiter'), NULL, 'rush', (SELECT payment_method_id FROM payment_method WHERE code = 'CARD'), DATE_SUB(NOW(), INTERVAL 5 MINUTE), NULL);

INSERT INTO order_item (order_id, dish_id, order_item_status_id, quantity, unit_price, assigned_cook_id, started_at, note) VALUES
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Том Ям'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'COOKING'), 1, 620.00, (SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'), DATE_SUB(NOW(), INTERVAL 18 MINUTE), 'Острее'),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Лимонад базилик-лайм'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'COOKING'), 1, 260.00, NULL, NULL, NULL),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-01') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Бургер GastroSoft'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'QUEUED'), 1, 670.00, NULL, NULL, 'Без лука'),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-01') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Тар-тар из лосося'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'QUEUED'), 1, 540.00, NULL, NULL, NULL);

INSERT INTO kitchen_log (order_id, action, performed_by_user_id, note) VALUES
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), 'CREATED', (SELECT user_id FROM app_user WHERE login = 'waiter'), 'Заказ создан'),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), 'ACCEPTED', (SELECT user_id FROM app_user WHERE login = 'chef'), 'Принят шеф-поваром'),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-01') ORDER BY order_id DESC LIMIT 1), 'CREATED', (SELECT user_id FROM app_user WHERE login = 'waiter'), 'Срочный заказ'),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-01') ORDER BY order_id DESC LIMIT 1), 'PRIORITY_SET', (SELECT user_id FROM app_user WHERE login = 'chef'), 'Приоритет: rush');
