import os
from dotenv import load_dotenv
load_dotenv()

import mysql.connector
from contextlib import contextmanager

@contextmanager
def connection():
    db = mysql.connector.connect(host=os.getenv('MYSQL_HOST','127.0.0.1'), port=int(os.getenv('MYSQL_PORT','3306')), user=os.getenv('MYSQL_USER','root'), password=os.getenv('MYSQL_PASSWORD',''), database=os.getenv('MYSQL_DATABASE','job_tracker'))
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def query(sql, params=(), one=False):
    with connection() as db:
        cursor=db.cursor(dictionary=True)
        try:
            cursor.execute(sql,params)
            return cursor.fetchone() if one else cursor.fetchall()
        finally: cursor.close()

def execute(sql, params=()):
    with connection() as db:
        cursor=db.cursor()
        try:
            cursor.execute(sql,params)
            return cursor.lastrowid
        finally: cursor.close()
