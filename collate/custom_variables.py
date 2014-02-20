'''A collection of tasks to perform related to Piwik custom variables.'''
import logging

import dbsources
import dbengine

class Populate(object):
    '''Take existing data and populate custom variables.'''
    def __init__(self):
        self.CONFIG = None # tables and fields to use
        self.CONNECTION = None # in this location
        self.setup()
        
    def setup(self):
        '''Setup the connection to the system being populated.'''
        source = dbsources.ReadWriteDB()
        source.setup_source1()
        host, username, password, database = source.get_settings()
        self.CONFIG = dbengine.PiwikConfig()
        self.CONNECTION = dbengine.Connection()
        self.CONNECTION.setup(host, username, password, database)
        
    def sql_count_customvar(self):
        count = self.CONFIG.FIELD_CUSTOM_VARS_SCODE
        table = self.CONFIG.TABLE_CUSTOM_VARS_STORE 
        return "SELECT COUNT(%s) FROM %s"%(count, table)
    
    def count_existing(self):
        '''Return the number of custom variables that exist.'''
        answer = self.CONNECTION.fetchone(self.sql_count_customvar())
        logging.info('Count of custom variable: %s'%answer)
        return answer
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    p = Populate()
    existing = p.count_existing()
    if existing:
        logging.critical('Data EXISTS in custom variables to populate.')
        logging.warn('If this is a new populate you need to check WHY.')
        
    