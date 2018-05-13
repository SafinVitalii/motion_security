from db.database import Database


class Model(object):
    def __init__(self, table='users'):
        self.db = Database()
        self.table = table

    def create(self, row):
        bindings = '('
        keys = '('
        values = []
        i = 0
        for key, value in row.items():
            if isinstance(value, str):
                bindings += '"{}"'.format(value)
            else:
                bindings += '{}'.format(value)
            keys += key
            values.append(value)
            i += 1
            if i != (len(row)):
                bindings += ', '
                keys += ', '
        bindings += ')'
        keys += ')'
        sql = 'INSERT INTO {} {} VALUES {};'.format(self.table, keys, bindings)
        print(sql)
        conn = self.db.connection()
        conn.execute(sql)
        conn.commit()

    def read_all(self):
        sql = 'SELECT * FROM {}'.format(self.table)
        print(sql)
        cursor = self.db.connection().execute(sql)
        rows = []
        for row in cursor:
            rows.append(row)
        return rows

    def read(self, email):
        sql = 'SELECT * FROM {} WHERE email="{}";'.format(self.table, email)
        print(sql)
        cursor = self.db.connection().execute(sql)
        rows = []
        for row in cursor:
            rows.append(row)
        return rows

    def update(self, row, where):
        keys = ''
        values = []
        i = 0
        for key, value in row.items():
            keys += key + ' = ?'
            values.append(value)
            i += 1
            if i != len(row):
                keys += ', '
        sql = 'UPDATE {} SET {} WHERE {} = {};'.format(self.table, keys, where['key'],
                                                       where['value'])
        print(sql, values)
        conn = self.db.connection()
        conn.execute(sql, values)
        conn.commit()

    def delete(self, where):
        sql = 'DELETE FROM {} WHERE {} = {};'.format(self.table, where['key'], where['value'])
        print(sql)
        conn = self.db.connection()
        conn.execute(sql)
        conn.commit()
