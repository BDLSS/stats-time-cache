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

class PiwikConfig(object):
    '''Configuration of tables and fields in Piwik.'''
    def __init__(self):
        links = 'piwik_log_link_visit_action'
        actions = 'piwik_log_action'
        self.TABLE_CUSTOM_VARS_STORE = links 
        self.TABLE_ACTION_LOOKUP = actions
        
        default = 5
        self.DEFAULT_CUSTOM_VARS = 5
        self.FIELD_CUSTOM_VARS_SCODE = self.config_variable(default)
        self.FIELD_CUSTOM_VARS_DCODE = self.config_variable(default, False)
        
        self.FIELD_ACTION_KEY = 'idaction'
        self.FIELD_ACTION_CONTAINS_CUSTOM_VAR = 'name'
        self.FIELD_ACTION_CONTAINS_DOWNLOAD = 'type'
        
        self.ACTION_ISUSEFUL = 1 # what counts as a view
        self.ACTION_ISDOWNLOAD = 3 # what counts as a download
        
        self.FIELD_STORE_KEY = 'idlink_va'
        self.FIELD_STORE_ACTION = '%s_url'%self.FIELD_ACTION_KEY
        self.FIELD_STORE_SITE = 'idsite'
        self.FIELD_STORE_TIME = 'server_time'
        self.FIELD_STORE_VISIT = 'idvisit'
    
    def setup_custom_vars(self, number):
        '''Set the custom variable used to store codes.'''
        self.FIELD_CUSTOM_VARS_SCODE = self.config_variable(number)
        self.FIELD_CUSTOM_VARS_DCODE = self.config_variable(number, False)
        
    def config_variable(self, number=5, usevalue=True):
        '''Set custom variable to use the numbered value column.'''
        if number not in range (1, 6): # Piwik has upto 5 custom vars
            number = self.DEFAULT_CUSTOM_VARS
        cat = 'v' # we will use the "value column of this custom var"
        if not usevalue:
            cat = 'k' # but you can use the key column instead.
        return 'custom_var_%s%s'%(cat, number)
    
    def get_action_look_config(self):
        '''Return the settings needed to lookup an action.'''
        return (self.TABLE_ACTION_LOOKUP,
                self.FIELD_ACTION_KEY,
                self.FIELD_ACTION_CONTAINS_CUSTOM_VAR,
                self.FIELD_ACTION_CONTAINS_DOWNLOAD)
        
    def get_store_look_config(self):
        return (self.TABLE_CUSTOM_VARS_STORE,
                self.FIELD_STORE_KEY,
                self.FIELD_STORE_ACTION,
                self.FIELD_STORE_SITE,
                self.FIELD_STORE_TIME,
                self.FIELD_STORE_VISIT,
                self.FIELD_CUSTOM_VARS_SCODE,
                self.FIELD_CUSTOM_VARS_DCODE,
                )
    
    def get_update_store_config(self):
        return (self.TABLE_CUSTOM_VARS_STORE, self.FIELD_STORE_KEY)
    
if __name__ == '__main__':
    rw = dbsources.ReadWriteDB()
    rw.setup_source1()
    host, user, passwd, database = rw.get_settings()
    
    dbc = Connection()
    dbc.setup(host, user, passwd, database)
    print dbc.fetchall('SELECT VERSION()')
    print "(('5.5.35-0ubuntu0.12.04.1',),) = connection okay"
    dbc.close()
    
    config = PiwikConfig()
    ats = dir(config)        
    for item in sorted(ats):
        if not str(item).startswith('_'):
            print item, '=', getattr(config, item)
            