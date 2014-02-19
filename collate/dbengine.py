'''Enable connection to database engine.'''
import logging
import MySQLdb as db

import dbsources # So we can use configuration options

class Connection(object):
    '''A connection to an external database.'''
    def __init__(self, ):
        self.HOST = ''
        self.USER = ''
        self.PASSWORD = ''
        self.DATABASE = ''
        self.CONNECTION = None # This connects to the DB
        
    def setup(self, host, username, password, database):
        '''Set username and password to connect to host database.'''
        self.HOST = host
        self.USER = username
        self.PASSWORD = password
        self.DATABASE = database
        logging.warn('DB to use: %s on %s with %s'%(database, host, username))
        
    def connect(self):
        '''Start a DB connection, reopening if necessary.'''        
        if not self.CONNECTION:
            try:
                self.CONNECTION = db.connect(host=self.HOST, user=self.USER,
                         passwd=self.PASSWORD, db=self.DATABASE)
                logging.debug('New connection to DB on: %s'%self.HOST)
                return True
            except db.OperationalError, e: #connection issue.
                logging.critical('Unable to connect to database')
                logging.critical('Exception: %s'%e)
                return False

    def cursor(self):
        '''Return a cursor to the database.'''
        if not self.CONNECTION:
            if not self.connect():
                return None
        return self.CONNECTION.cursor()
    
    def fetchall(self, query):
        logging.debug('Fetch all query: %s'%query)
        cursor = self.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    
    def fetchone(self, query):
        logging.debug('Fetch one query: %s'%query)
        cursor = self.cursor()
        cursor.execute(query)
        return cursor.fetchone()
        
    def close(self):
        '''Close the DB connection if required.'''
        if self.CONNECTION:
            logging.debug('Closing connection')
            self.CONNECTION.close()

if __name__ == '__main__':
    rw = dbsources.ReadWriteDB()
    rw.setup_source1()
    host, user, passwd, database = rw.get_settings()
    
    dbc = Connection()
    dbc.setup(host, user, passwd, database)
    print dbc.fetchall('SELECT VERSION()')
    print "(('5.5.35-0ubuntu0.12.04.1',),) = connection okay"
    dbc.close()
    