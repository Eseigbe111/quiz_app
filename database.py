import sqlite3 # this contains our database created
from flask import g # This is a global variable used for database connection


def connect_to_database():
    """ 
    As the name implies, it connects to the database to get the data stored
    """
    sql = sqlite3.connect("C:/Users/GUDNES/Desktop/quiz_app/quizapp.db") # connecting to the database
    sql.row_factory = sqlite3.Row # converting the database to a row
    return sql


def getDatabase():
    """ 
    This function will return us to the database we have connected to
    """
    if not hasattr(g, "quizapp_db"): # checking if the global variable g does not have a quizapp_db, so that it can connect to the connect_to_database() to get it
        g.quizapp_db = connect_to_database()
    return g.quizapp_db