-- GastroSoft course project
-- MySQL 8+ / MariaDB-compatible schema
-- Goal: restaurant operations + staff planning in 3NF

DROP DATABASE IF EXISTS gastrosoft_course;
CREATE DATABASE gastrosoft_course
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE gastrosoft_course;

-- =========================================================
-- Reference tables
-- =========================================================

CREATE TABLE employee_role (
  role_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_role_code (code),
  UNIQUE KEY uq_role_name (name)
) ENGINE=InnoDB;

CREATE TABLE skill (
  skill_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (skill_id),
  UNIQUE KEY uq_skill_name (name)
) ENGINE=InnoDB;

CREATE TABLE shift_type (
  shift_type_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  default_start_time TIME DEFAULT NULL,
  default_end_time TIME DEFAULT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (shift_type_id),
  UNIQUE KEY uq_shift_type_code (code),
  UNIQUE KEY uq_shift_type_name (name)
) ENGINE=InnoDB;

CREATE TABLE shift_status (
  shift_status_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (shift_status_id),
  UNIQUE KEY uq_shift_status_code (code),
  UNIQUE KEY uq_shift_status_name (name)
) ENGINE=InnoDB;

CREATE TABLE swap_request_status (
  swap_request_status_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (swap_request_status_id),
  UNIQUE KEY uq_swap_request_status_code (code),
  UNIQUE KEY uq_swap_request_status_name (name)
) ENGINE=InnoDB;

CREATE TABLE reservation_status (
  reservation_status_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (reservation_status_id),
  UNIQUE KEY uq_reservation_status_code (code),
  UNIQUE KEY uq_reservation_status_name (name)
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

CREATE TABLE measurement_unit (
  measurement_unit_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  name VARCHAR(50) NOT NULL,
  description VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (measurement_unit_id),
  UNIQUE KEY uq_measurement_unit_code (code),
  UNIQUE KEY uq_measurement_unit_name (name)
) ENGINE=InnoDB;

-- =========================================================
-- Employees and access
-- =========================================================

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

CREATE TABLE employee_skill (
  employee_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  skill_level TINYINT UNSIGNED NOT NULL DEFAULT 1,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (employee_id, skill_id),
  KEY idx_employee_skill_skill (skill_id),
  CONSTRAINT fk_employee_skill_employee
    FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_employee_skill_skill
    FOREIGN KEY (skill_id) REFERENCES skill (skill_id)
) ENGINE=InnoDB;

CREATE TABLE employee_shift_preference (
  employee_id INT UNSIGNED NOT NULL,
  shift_type_id INT UNSIGNED NOT NULL,
  preference_level TINYINT UNSIGNED NOT NULL DEFAULT 3,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (employee_id, shift_type_id),
  KEY idx_employee_shift_preference_type (shift_type_id),
  CONSTRAINT fk_employee_shift_preference_employee
    FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_employee_shift_preference_type
    FOREIGN KEY (shift_type_id) REFERENCES shift_type (shift_type_id)
) ENGINE=InnoDB;

-- =========================================================
-- Hall, guests, reservations, forecasts
-- =========================================================

CREATE TABLE restaurant_table (
  table_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  seats_count TINYINT UNSIGNED NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (table_id),
  UNIQUE KEY uq_restaurant_table_code (code)
) ENGINE=InnoDB;

CREATE TABLE guest (
  guest_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  email VARCHAR(100) DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (guest_id),
  KEY idx_guest_name (full_name),
  KEY idx_guest_phone (phone)
) ENGINE=InnoDB;

CREATE TABLE reservation (
  reservation_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  guest_id INT UNSIGNED NOT NULL,
  table_id INT UNSIGNED DEFAULT NULL,
  reservation_status_id INT UNSIGNED NOT NULL,
  reserved_from DATETIME NOT NULL,
  reserved_to DATETIME NOT NULL,
  guest_count TINYINT UNSIGNED NOT NULL,
  created_by_user_id INT UNSIGNED NOT NULL,
  note VARCHAR(255) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (reservation_id),
  KEY idx_reservation_guest (guest_id),
  KEY idx_reservation_table (table_id),
  KEY idx_reservation_status (reservation_status_id),
  KEY idx_reservation_datetime (reserved_from, reserved_to),
  KEY idx_reservation_created_by (created_by_user_id),
  CONSTRAINT fk_reservation_guest
    FOREIGN KEY (guest_id) REFERENCES guest (guest_id),
  CONSTRAINT fk_reservation_table
    FOREIGN KEY (table_id) REFERENCES restaurant_table (table_id),
  CONSTRAINT fk_reservation_status
    FOREIGN KEY (reservation_status_id) REFERENCES reservation_status (reservation_status_id),
  CONSTRAINT fk_reservation_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES app_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE workload_forecast (
  forecast_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  forecast_start DATETIME NOT NULL,
  forecast_end DATETIME NOT NULL,
  expected_guests INT UNSIGNED NOT NULL,
  expected_orders INT UNSIGNED NOT NULL,
  hall_load_percent DECIMAL(5,2) NOT NULL,
  kitchen_load_percent DECIMAL(5,2) NOT NULL,
  created_by_user_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (forecast_id),
  KEY idx_workload_forecast_period (forecast_start, forecast_end),
  KEY idx_workload_forecast_created_by (created_by_user_id),
  CONSTRAINT fk_workload_forecast_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES app_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE staffing_requirement (
  forecast_id INT UNSIGNED NOT NULL,
  role_id INT UNSIGNED NOT NULL,
  required_employee_count TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (forecast_id, role_id),
  KEY idx_staffing_requirement_role (role_id),
  CONSTRAINT fk_staffing_requirement_forecast
    FOREIGN KEY (forecast_id) REFERENCES workload_forecast (forecast_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_staffing_requirement_role
    FOREIGN KEY (role_id) REFERENCES employee_role (role_id)
) ENGINE=InnoDB;

-- =========================================================
-- Shift planning and time tracking
-- =========================================================

CREATE TABLE work_shift (
  shift_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  shift_type_id INT UNSIGNED NOT NULL,
  shift_status_id INT UNSIGNED NOT NULL,
  planned_start DATETIME NOT NULL,
  planned_end DATETIME NOT NULL,
  created_by_user_id INT UNSIGNED NOT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (shift_id),
  KEY idx_work_shift_type (shift_type_id),
  KEY idx_work_shift_status (shift_status_id),
  KEY idx_work_shift_period (planned_start, planned_end),
  KEY idx_work_shift_created_by (created_by_user_id),
  CONSTRAINT fk_work_shift_type
    FOREIGN KEY (shift_type_id) REFERENCES shift_type (shift_type_id),
  CONSTRAINT fk_work_shift_status
    FOREIGN KEY (shift_status_id) REFERENCES shift_status (shift_status_id),
  CONSTRAINT fk_work_shift_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES app_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE shift_assignment (
  assignment_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  shift_id INT UNSIGNED NOT NULL,
  employee_id INT UNSIGNED NOT NULL,
  assignment_role_id INT UNSIGNED NOT NULL,
  check_in_time DATETIME DEFAULT NULL,
  check_out_time DATETIME DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (assignment_id),
  UNIQUE KEY uq_shift_assignment (shift_id, employee_id),
  KEY idx_shift_assignment_employee (employee_id),
  KEY idx_shift_assignment_role (assignment_role_id),
  CONSTRAINT fk_shift_assignment_shift
    FOREIGN KEY (shift_id) REFERENCES work_shift (shift_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_shift_assignment_employee
    FOREIGN KEY (employee_id) REFERENCES employee (employee_id),
  CONSTRAINT fk_shift_assignment_role
    FOREIGN KEY (assignment_role_id) REFERENCES employee_role (role_id)
) ENGINE=InnoDB;

CREATE TABLE shift_swap_request (
  swap_request_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  assignment_id INT UNSIGNED NOT NULL,
  requested_employee_id INT UNSIGNED DEFAULT NULL,
  swap_request_status_id INT UNSIGNED NOT NULL,
  requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at DATETIME DEFAULT NULL,
  decided_by_user_id INT UNSIGNED DEFAULT NULL,
  reason VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (swap_request_id),
  KEY idx_shift_swap_request_assignment (assignment_id),
  KEY idx_shift_swap_request_employee (requested_employee_id),
  KEY idx_shift_swap_request_status (swap_request_status_id),
  KEY idx_shift_swap_request_decided_by (decided_by_user_id),
  CONSTRAINT fk_shift_swap_request_assignment
    FOREIGN KEY (assignment_id) REFERENCES shift_assignment (assignment_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_shift_swap_request_employee
    FOREIGN KEY (requested_employee_id) REFERENCES employee (employee_id),
  CONSTRAINT fk_shift_swap_request_status
    FOREIGN KEY (swap_request_status_id) REFERENCES swap_request_status (swap_request_status_id),
  CONSTRAINT fk_shift_swap_request_decided_by
    FOREIGN KEY (decided_by_user_id) REFERENCES app_user (user_id)
) ENGINE=InnoDB;

-- =========================================================
-- Menu, modifiers, recipes
-- =========================================================

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
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_dish_modifier_group_group
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_group (modifier_group_id)
      ON DELETE CASCADE
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
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_group (modifier_group_id)
      ON DELETE CASCADE
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
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_recipe_item_ingredient
    FOREIGN KEY (ingredient_id) REFERENCES ingredient (ingredient_id)
) ENGINE=InnoDB;

-- =========================================================
-- Orders and stock movement
-- =========================================================

CREATE TABLE customer_order (
  order_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  table_id INT UNSIGNED DEFAULT NULL,
  reservation_id INT UNSIGNED DEFAULT NULL,
  order_status_id INT UNSIGNED NOT NULL,
  created_by_user_id INT UNSIGNED NOT NULL,
  payment_method_id INT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  closed_at DATETIME DEFAULT NULL,
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (order_id),
  KEY idx_customer_order_table (table_id),
  KEY idx_customer_order_reservation (reservation_id),
  KEY idx_customer_order_status (order_status_id),
  KEY idx_customer_order_created_by (created_by_user_id),
  KEY idx_customer_order_payment_method (payment_method_id),
  KEY idx_customer_order_created_at (created_at),
  CONSTRAINT fk_customer_order_table
    FOREIGN KEY (table_id) REFERENCES restaurant_table (table_id),
  CONSTRAINT fk_customer_order_reservation
    FOREIGN KEY (reservation_id) REFERENCES reservation (reservation_id),
  CONSTRAINT fk_customer_order_status
    FOREIGN KEY (order_status_id) REFERENCES order_status (order_status_id),
  CONSTRAINT fk_customer_order_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES app_user (user_id),
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
  note VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (order_item_id),
  KEY idx_order_item_order (order_id),
  KEY idx_order_item_dish (dish_id),
  KEY idx_order_item_status (order_item_status_id),
  CONSTRAINT fk_order_item_order
    FOREIGN KEY (order_id) REFERENCES customer_order (order_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_order_item_dish
    FOREIGN KEY (dish_id) REFERENCES dish (dish_id),
  CONSTRAINT fk_order_item_status
    FOREIGN KEY (order_item_status_id) REFERENCES order_item_status (order_item_status_id)
) ENGINE=InnoDB;

CREATE TABLE order_item_modifier (
  order_item_id INT UNSIGNED NOT NULL,
  modifier_option_id INT UNSIGNED NOT NULL,
  extra_charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (order_item_id, modifier_option_id),
  KEY idx_order_item_modifier_option (modifier_option_id),
  CONSTRAINT fk_order_item_modifier_order_item
    FOREIGN KEY (order_item_id) REFERENCES order_item (order_item_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_order_item_modifier_option
    FOREIGN KEY (modifier_option_id) REFERENCES modifier_option (modifier_option_id)
) ENGINE=InnoDB;

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

-- =========================================================
-- Useful analytical views
-- =========================================================

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

CREATE OR REPLACE VIEW v_shift_assignment_hours AS
SELECT
  sa.assignment_id,
  sa.shift_id,
  sa.employee_id,
  sa.assignment_role_id,
  TIMESTAMPDIFF(
    MINUTE,
    ws.planned_start,
    ws.planned_end
  ) / 60.0 AS planned_hours,
  CASE
    WHEN sa.check_in_time IS NOT NULL AND sa.check_out_time IS NOT NULL
      THEN TIMESTAMPDIFF(MINUTE, sa.check_in_time, sa.check_out_time) / 60.0
    ELSE NULL
  END AS actual_hours
FROM shift_assignment sa
JOIN work_shift ws
  ON ws.shift_id = sa.shift_id;

-- =========================================================
-- Basic reference data
-- =========================================================

INSERT INTO employee_role (code, name, description) VALUES
  ('ADMIN', 'Administrator', 'Full access to the system'),
  ('DIRECTOR', 'Director', 'Controls efficiency and approves plans'),
  ('CHEF', 'Chef', 'Manages kitchen operations'),
  ('HALL_MANAGER', 'Hall manager', 'Coordinates front-of-house staff'),
  ('ACCOUNTANT', 'Accountant', 'Works with payroll and reports'),
  ('WAITER', 'Waiter', 'Serves guests'),
  ('COOK', 'Cook', 'Prepares dishes'),
  ('CASHIER', 'Cashier', 'Works with payments and closing');

INSERT INTO shift_type (code, name, default_start_time, default_end_time, description) VALUES
  ('MORNING', 'Morning shift', '08:00:00', '14:00:00', 'Morning work period'),
  ('DAY', 'Day shift', '12:00:00', '18:00:00', 'Main daytime work period'),
  ('EVENING', 'Evening shift', '17:00:00', '23:00:00', 'Evening work period'),
  ('NIGHT', 'Night shift', '22:00:00', '06:00:00', 'Night work period');

INSERT INTO shift_status (code, name) VALUES
  ('PLANNED', 'Planned'),
  ('IN_PROGRESS', 'In progress'),
  ('COMPLETED', 'Completed'),
  ('CANCELLED', 'Cancelled');

INSERT INTO swap_request_status (code, name) VALUES
  ('NEW', 'New'),
  ('APPROVED', 'Approved'),
  ('REJECTED', 'Rejected'),
  ('CANCELLED', 'Cancelled');

INSERT INTO reservation_status (code, name) VALUES
  ('ACTIVE', 'Active'),
  ('PENDING', 'Pending'),
  ('CONFIRMED', 'Confirmed'),
  ('SEATED', 'Seated'),
  ('COMPLETED', 'Completed'),
  ('CANCELLED', 'Cancelled'),
  ('NO_SHOW', 'No show');

INSERT INTO order_status (code, name) VALUES
  ('NEW', 'New'),
  ('ACCEPTED', 'Accepted'),
  ('PREPARING', 'Preparing'),
  ('READY', 'Ready'),
  ('SERVED', 'Served'),
  ('CLOSED', 'Closed'),
  ('CANCELLED', 'Cancelled');

INSERT INTO order_item_status (code, name) VALUES
  ('QUEUED', 'Queued'),
  ('COOKING', 'Cooking'),
  ('READY', 'Ready'),
  ('SERVED', 'Served'),
  ('CANCELLED', 'Cancelled');

INSERT INTO payment_method (code, name) VALUES
  ('CASH', 'Cash'),
  ('CARD', 'Card'),
  ('ONLINE', 'Online');

INSERT INTO stock_operation_type (code, name, operation_sign) VALUES
  ('RECEIPT', 'Receipt', 1),
  ('WRITE_OFF', 'Write-off', -1),
  ('ADJUSTMENT_IN', 'Adjustment increase', 1),
  ('ADJUSTMENT_OUT', 'Adjustment decrease', -1);

INSERT INTO measurement_unit (code, name, description) VALUES
  ('g', 'Gram', 'Weight in grams'),
  ('kg', 'Kilogram', 'Weight in kilograms'),
  ('ml', 'Milliliter', 'Volume in milliliters'),
  ('l', 'Liter', 'Volume in liters'),
  ('pcs', 'Piece', 'Countable unit');

-- =========================================================
-- Application seed data
-- =========================================================

INSERT INTO skill (name, description) VALUES
  ('Аналитика', 'Работа с показателями и отчетами'),
  ('Горячий цех', 'Приготовление горячих блюд'),
  ('Гости VIP', 'Обслуживание важных гостей'),
  ('Закрытие смены', 'Кассовая дисциплина и закрытие дня'),
  ('Бронирования', 'Организация посадки гостей'),
  ('Холодный цех', 'Приготовление холодных блюд'),
  ('Гриль', 'Работа с гриль-станцией'),
  ('Отчеты', 'Финансовые и складские отчеты');

INSERT INTO employee (role_id, last_name, first_name, middle_name, phone, email, hire_date, is_active) VALUES
  ((SELECT role_id FROM employee_role WHERE code = 'DIRECTOR'), 'Смирнова', 'Анна', NULL, '+7 900 100-10-01', 'director@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'CHEF'), 'Волков', 'Илья', NULL, '+7 900 100-10-02', 'chef@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'WAITER'), 'Белова', 'Мария', NULL, '+7 900 100-10-03', 'waiter@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'CASHIER'), 'Корнеев', 'Олег', NULL, '+7 900 100-10-04', 'cashier@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'HALL_MANAGER'), 'Орлова', 'Ксения', NULL, '+7 900 100-10-05', 'hall@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'COOK'), 'Громов', 'Павел', NULL, '+7 900 100-10-06', 'cook1@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'COOK'), 'Котов', 'Даниил', NULL, '+7 900 100-10-07', 'cook2@gastrosoft.local', CURRENT_DATE(), 1),
  ((SELECT role_id FROM employee_role WHERE code = 'ACCOUNTANT'), 'Руднева', 'Светлана', NULL, '+7 900 100-10-08', 'accountant@gastrosoft.local', CURRENT_DATE(), 1);

INSERT INTO employee_skill (employee_id, skill_id, skill_level) VALUES
  ((SELECT employee_id FROM employee WHERE email = 'director@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Аналитика'), 5),
  ((SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Горячий цех'), 5),
  ((SELECT employee_id FROM employee WHERE email = 'waiter@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Гости VIP'), 4),
  ((SELECT employee_id FROM employee WHERE email = 'cashier@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Закрытие смены'), 4),
  ((SELECT employee_id FROM employee WHERE email = 'hall@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Бронирования'), 5),
  ((SELECT employee_id FROM employee WHERE email = 'cook1@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Холодный цех'), 4),
  ((SELECT employee_id FROM employee WHERE email = 'cook2@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Гриль'), 4),
  ((SELECT employee_id FROM employee WHERE email = 'accountant@gastrosoft.local'), (SELECT skill_id FROM skill WHERE name = 'Отчеты'), 5);

INSERT INTO app_user (employee_id, login, password_hash, is_active) VALUES
  ((SELECT employee_id FROM employee WHERE email = 'director@gastrosoft.local'), 'director', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'), 'chef', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'cook1@gastrosoft.local'), 'cook', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'waiter@gastrosoft.local'), 'waiter', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1),
  ((SELECT employee_id FROM employee WHERE email = 'cashier@gastrosoft.local'), 'cashier', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 1);

INSERT INTO restaurant_table (code, seats_count, is_active, note) VALUES
  ('T-01', 2, 1, 'Window table'),
  ('T-02', 2, 1, 'Bar area'),
  ('T-03', 4, 1, 'Main hall'),
  ('T-04', 4, 1, 'Main hall'),
  ('T-05', 6, 1, 'Family table'),
  ('T-06', 6, 1, 'VIP corner');

INSERT INTO guest (full_name, phone) VALUES
  ('Екатерина Миронова', '+7 912 555-11-22'),
  ('Денис Петров', '+7 922 100-50-40');

INSERT INTO reservation (
  guest_id,
  table_id,
  reservation_status_id,
  reserved_from,
  reserved_to,
  guest_count,
  created_by_user_id
) VALUES
  (
    (SELECT guest_id FROM guest WHERE phone = '+7 912 555-11-22'),
    (SELECT table_id FROM restaurant_table WHERE code = 'T-06'),
    (SELECT reservation_status_id FROM reservation_status WHERE code = 'CONFIRMED'),
    DATE_ADD(NOW(), INTERVAL 1 HOUR),
    DATE_ADD(NOW(), INTERVAL 3 HOUR),
    5,
    (SELECT user_id FROM app_user WHERE login = 'director')
  ),
  (
    (SELECT guest_id FROM guest WHERE phone = '+7 922 100-50-40'),
    (SELECT table_id FROM restaurant_table WHERE code = 'T-02'),
    (SELECT reservation_status_id FROM reservation_status WHERE code = 'PENDING'),
    DATE_ADD(NOW(), INTERVAL 2 HOUR),
    DATE_ADD(NOW(), INTERVAL 4 HOUR),
    2,
    (SELECT user_id FROM app_user WHERE login = 'director')
  );

INSERT INTO menu_category (name, description, sort_order) VALUES
  ('Закуски', 'Small plates and starters', 10),
  ('Супы', 'Soups', 20),
  ('Горячее', 'Main dishes', 30),
  ('Напитки', 'Drinks', 40);

INSERT INTO dish (category_id, name, description, base_price, prep_time_minutes, is_active) VALUES
  ((SELECT category_id FROM menu_category WHERE name = 'Закуски'), 'Брускетта с томатами', 'Хрустящий хлеб с томатами и базиликом', 390.00, 7, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Закуски'), 'Тар-тар из лосося', 'Лосось с соусом и зеленью', 540.00, 10, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Супы'), 'Том Ям', 'Острый суп с морепродуктами', 620.00, 12, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Супы'), 'Крем-суп из грибов', 'Грибной крем-суп со сливками', 430.00, 9, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Горячее'), 'Паста Альфредо', 'Паста со сливочным соусом', 590.00, 15, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Горячее'), 'Бургер GastroSoft', 'Фирменный бургер с котлетой', 670.00, 14, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Напитки'), 'Лимонад базилик-лайм', 'Домашний лимонад', 260.00, 3, 1),
  ((SELECT category_id FROM menu_category WHERE name = 'Напитки'), 'Эспрессо', 'Классический кофе', 170.00, 2, 1);

INSERT INTO ingredient (measurement_unit_id, name, cost_per_unit, critical_level, is_active) VALUES
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Томаты', 180.00, 5.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'l'), 'Сливки', 220.00, 3.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Лосось', 1300.00, 2.500, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'pcs'), 'Булочки бриошь', 45.00, 10.000, 1),
  ((SELECT measurement_unit_id FROM measurement_unit WHERE code = 'kg'), 'Кофе зерно', 900.00, 1.500, 1);

INSERT INTO inventory_operation (ingredient_id, stock_operation_type_id, quantity, performed_by_user_id, note) VALUES
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Томаты'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 4.600, (SELECT user_id FROM app_user WHERE login = 'director'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Сливки'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 7.500, (SELECT user_id FROM app_user WHERE login = 'director'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Лосось'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 3.100, (SELECT user_id FROM app_user WHERE login = 'director'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Булочки бриошь'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 14.000, (SELECT user_id FROM app_user WHERE login = 'director'), 'Начальный остаток'),
  ((SELECT ingredient_id FROM ingredient WHERE name = 'Кофе зерно'), (SELECT stock_operation_type_id FROM stock_operation_type WHERE code = 'RECEIPT'), 2.200, (SELECT user_id FROM app_user WHERE login = 'director'), 'Начальный остаток');

INSERT INTO work_shift (shift_type_id, shift_status_id, planned_start, planned_end, created_by_user_id) VALUES
  ((SELECT shift_type_id FROM shift_type WHERE code = 'MORNING'), (SELECT shift_status_id FROM shift_status WHERE code = 'IN_PROGRESS'), TIMESTAMP(CURRENT_DATE(), '08:00:00'), TIMESTAMP(CURRENT_DATE(), '14:00:00'), (SELECT user_id FROM app_user WHERE login = 'director')),
  ((SELECT shift_type_id FROM shift_type WHERE code = 'DAY'), (SELECT shift_status_id FROM shift_status WHERE code = 'PLANNED'), TIMESTAMP(CURRENT_DATE(), '12:00:00'), TIMESTAMP(CURRENT_DATE(), '18:00:00'), (SELECT user_id FROM app_user WHERE login = 'director'));

INSERT INTO shift_assignment (shift_id, employee_id, assignment_role_id, check_in_time) VALUES
  (
    (SELECT shift_id FROM work_shift WHERE planned_start = TIMESTAMP(CURRENT_DATE(), '08:00:00') LIMIT 1),
    (SELECT employee_id FROM employee WHERE email = 'chef@gastrosoft.local'),
    (SELECT role_id FROM employee_role WHERE code = 'CHEF'),
    TIMESTAMP(CURRENT_DATE(), '08:00:00')
  ),
  (
    (SELECT shift_id FROM work_shift WHERE planned_start = TIMESTAMP(CURRENT_DATE(), '12:00:00') LIMIT 1),
    (SELECT employee_id FROM employee WHERE email = 'waiter@gastrosoft.local'),
    (SELECT role_id FROM employee_role WHERE code = 'WAITER'),
    NULL
  );

INSERT INTO customer_order (table_id, order_status_id, created_by_user_id, payment_method_id, created_at, closed_at) VALUES
  ((SELECT table_id FROM restaurant_table WHERE code = 'T-03'), (SELECT order_status_id FROM order_status WHERE code = 'PREPARING'), (SELECT user_id FROM app_user WHERE login = 'waiter'), (SELECT payment_method_id FROM payment_method WHERE code = 'CARD'), DATE_SUB(NOW(), INTERVAL 20 MINUTE), NULL),
  ((SELECT table_id FROM restaurant_table WHERE code = 'T-02'), (SELECT order_status_id FROM order_status WHERE code = 'CLOSED'), (SELECT user_id FROM app_user WHERE login = 'cashier'), (SELECT payment_method_id FROM payment_method WHERE code = 'CASH'), DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 1 HOUR));

INSERT INTO order_item (order_id, dish_id, order_item_status_id, quantity, unit_price) VALUES
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Том Ям'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'COOKING'), 1, 620.00),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-03') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Лимонад базилик-лайм'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'COOKING'), 1, 260.00),
  ((SELECT order_id FROM customer_order WHERE table_id = (SELECT table_id FROM restaurant_table WHERE code = 'T-02') ORDER BY order_id DESC LIMIT 1), (SELECT dish_id FROM dish WHERE name = 'Паста Альфредо'), (SELECT order_item_status_id FROM order_item_status WHERE code = 'SERVED'), 2, 590.00);
