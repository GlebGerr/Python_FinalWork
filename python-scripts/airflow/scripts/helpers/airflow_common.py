def get_connection_uri(conn):
    """
    Создает валидный URI из параметров хука.

    Args:
        conn: Соединение, полученное из хука.

    Returns:
        str: Строка URI для подключения к СУБД.
    """
    conn_type_jdbc_mapping = {
        "postgres": "postgresql",
        "mysql": "mysql"
    }

    conn_type = conn_type_jdbc_mapping.get(conn.conn_type)
    if not conn_type:
        raise ValueError(f"Unsupported connection type: {conn.conn_type}")

    login = conn.login
    password = conn.password
    host = conn.host
    port = conn.port
    db = conn.schema

    extras_list = [f"{k}={v}" for k, v in conn.extra_dejson.items()]
    extras = f"&{'&'.join(extras_list)}" if extras_list else ''

    return f"jdbc:{conn_type}://{host}:{port}/{db}?user={login}&password={password}{extras}"
