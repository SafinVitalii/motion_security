import sqlite3

sql_create_users_table = "CREATE TABLE IF NOT EXISTS users" \
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT ,password text NOT NULL, " \
                         "email text NOT NULL);"


class Database(object):
    def __init__(self, db_file='samplename.db'):
        self.db_file = db_file

    def connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except sqlite3.Error as e:
            print(e)

        return None

    def setup(self):
        connection = self.connection()
        if not connection:
            print("Error! cannot create the database connection.")

        else:
            self._create_table(connection, sql_create_users_table)

    def _create_table(self, conn, create_table_sql):
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except sqlite3.Error as e:
            print(e)
