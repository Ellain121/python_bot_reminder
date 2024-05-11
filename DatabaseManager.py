import sqlite3
import atexit
from datetime import datetime
from sqlite3 import Cursor
from typing import Any, List

DATABASE_FILE = "./data/tasks.db"
TABLE_NAME = "tasks"
CREATE_TABLE_QUERY =  \
    "CREATE TABLE IF NOT EXISTS " \
    + TABLE_NAME + \
    " (id INTEGER PRIMARY KEY AUTOINCREMENT,"\
    "text TEXT NOT NULL,"\
    "add_date INT NOT NULL"\
    ");"


def isQueryError(cursor: Cursor):
    print(cursor.fetchall())
    return cursor.fetchall() is None


class Entry():
    task: str
    add_date: int

    def __init__(self, task: str):
        self.task = task
        self.add_date = int(datetime.now().timestamp())


class DatabaseManager():
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.connection.cursor()
        atexit.register(self.cleanup)
        self.createTable()

    def cleanup(self):
        print("Bye!")
        self.cursor.close()
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def createTable(self):
        self.cursor.execute(CREATE_TABLE_QUERY)
        if isQueryError(self.cursor):
            print("Error 404")

    def addEntry(self, entry: Entry):
        query_str = "INSERT INTO " \
            + TABLE_NAME \
            + " (text, add_date) VALUES (?, ?);"
        self.cursor.execute(query_str, (entry.task, entry.add_date))
        if isQueryError(self.cursor):
            print("Error 418 I am a teapot")

    def delEntries(self, ids: List[str]):
        query_str = "DELETE FROM " \
            + TABLE_NAME \
            + " WHERE id=(?)"
        for i in range(len(ids)):
            ids[i] = (ids[i],)
        print(f"hERE f{ids}")

        self.cursor.executemany(query_str, ids)
        if isQueryError(self.cursor):
            print("Error 505")

    def delEntry(self, id: int):
        query_str = "DELETE FROM "\
            + TABLE_NAME \
            + " WHERE id=(?);"
        self.cursor.execute(query_str, (id))
        if isQueryError(self.cursor):
            print("Error 500")

    def delEntry(self, task: str):
        query_str = "DELETE FROM "\
            + TABLE_NAME
        + " WHERE text=(?);"
        self.cursor.execute(query_str, (task))
        if isQueryError(self.cursor):
            print("Error 400")

    def getEntries(self) -> List[Any]:
        query_str = "SELECT * FROM " + TABLE_NAME + ";"
        self.cursor.execute(query_str)
        return self.cursor.fetchall()
