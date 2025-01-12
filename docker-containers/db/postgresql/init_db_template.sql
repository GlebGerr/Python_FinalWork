-- БД, юзер и гранты
CREATE DATABASE ${POSTGRESQL_APP_DB};
CREATE USER ${POSTGRESQL_APP_USER} WITH PASSWORD '${POSTGRESQL_APP_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRESQL_APP_DB} TO ${POSTGRESQL_APP_USER};

-- Подключение к БД
\c ${POSTGRESQL_APP_DB}

-- Создание схемы, изменение дефолтной схемы и гранты
CREATE SCHEMA IF NOT EXISTS ${POSTGRESQL_APP_SCHEMA} AUTHORIZATION ${POSTGRESQL_APP_USER};
SET search_path TO ${POSTGRESQL_APP_SCHEMA};

-- Назначение прав на объекты схемы
ALTER DEFAULT PRIVILEGES IN SCHEMA ${POSTGRESQL_APP_SCHEMA} GRANT ALL PRIVILEGES ON TABLES TO ${POSTGRESQL_APP_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA ${POSTGRESQL_APP_SCHEMA} GRANT USAGE ON SEQUENCES TO ${POSTGRESQL_APP_USER};

-- Создание таблицы users
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date TIMESTAMP NOT NULL,
    loyalty_status VARCHAR(20) CHECK (loyalty_status IN ('Gold', 'Silver', 'Bronze'))
);

-- Создание таблицы productcategories
CREATE TABLE IF NOT EXISTS productcategories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_category_id INT REFERENCES productcategories(category_id) ON DELETE SET NULL
);

-- Создание таблицы products
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INT REFERENCES productcategories(category_id) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INT NOT NULL CHECK (stock_quantity >= 0),
    creation_date TIMESTAMP DEFAULT NOW()
);

-- Создание таблицы orders
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    order_date TIMESTAMP NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Pending', 'Completed', 'Canceled', 'Processing', 'Shipped', 'Delivered', 'Returned', 'Failed')),
    delivery_date TIMESTAMP
);

-- Создание таблицы orderdetails
CREATE TABLE IF NOT EXISTS orderdetails (
    order_detail_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity > 0),
    price_per_unit NUMERIC(10, 2) NOT NULL CHECK (price_per_unit >= 0),
    total_price NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0)
);

-- Создание таблицы reviews
CREATE TABLE IF NOT EXISTS reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы loyaltypoints
CREATE TABLE IF NOT EXISTS loyaltypoints (
    loyalty_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    points INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы аудита
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    change_id BIGSERIAL UNIQUE,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    user_id INT,
    operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB,
    is_processed BOOLEAN DEFAULT FALSE
);

-- Создание универсальной функции для логирования изменений
CREATE OR REPLACE FUNCTION log_table_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log(table_name, operation, user_id, new_data)
        VALUES (TG_TABLE_NAME, 'INSERT', NULL, row_to_json(NEW)::JSONB);
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log(table_name, operation, user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'UPDATE', NULL, row_to_json(OLD)::JSONB, row_to_json(NEW)::JSONB);
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log(table_name, operation, user_id, old_data)
        VALUES (TG_TABLE_NAME, 'DELETE', NULL, row_to_json(OLD)::JSONB);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Создание триггеров для всех таблиц
CREATE TRIGGER trg_users_audit
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_productcategories_audit
AFTER INSERT ON productcategories
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_products_audit
AFTER INSERT ON products
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_orders_audit
AFTER INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_orderdetails_audit
AFTER INSERT ON orderdetails
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_reviews_audit
AFTER INSERT ON reviews
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

CREATE TRIGGER trg_loyaltypoints_audit
AFTER INSERT ON loyaltypoints
FOR EACH ROW EXECUTE FUNCTION log_table_changes();

-- Индексы для ускорения выборок
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orderdetails_order_id ON orderdetails(order_id);
CREATE INDEX IF NOT EXISTS idx_orderdetails_product_id ON orderdetails(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_loyaltypoints_user_id ON loyaltypoints(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_change_id ON audit_log(change_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_is_processed ON audit_log(is_processed);


-- Функция для получения необработанных изменений
CREATE OR REPLACE FUNCTION get_unprocessed_changes()
RETURNS TABLE(
    change_id BIGINT,
    table_name VARCHAR(255),
    operation VARCHAR(50),
    user_id INT,
    operation_time TIMESTAMP,
    old_data JSONB,
    new_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT change_id, table_name, operation, user_id, operation_time, old_data, new_data
    FROM ${POSTGRESQL_APP_SCHEMA}.audit_log
    WHERE is_processed = FALSE
    ORDER BY change_id;
END;
$$ LANGUAGE plpgsql;

-- Функция для отметки изменений как обработанных
CREATE OR REPLACE FUNCTION mark_changes_as_processed(max_change_id BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE ${POSTGRESQL_APP_SCHEMA}.audit_log
    SET is_processed = TRUE
    WHERE change_id <= max_change_id AND is_processed = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Пример использования:
-- Получить все необработанные изменения:
-- SELECT * FROM get_unprocessed_changes();

-- Отметить изменения до определенного change_id как обработанные:
-- SELECT mark_changes_as_processed(100);