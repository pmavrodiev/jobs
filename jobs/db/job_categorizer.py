# -*- coding: utf-8 -*-

    def read_sqlite(self):
        self.db_reader.open_db()
        all_rows = self.db_reader.runQuery('SELECT * FROM bgjobs')
        self.db_reader.close_db()
        return all_rows
