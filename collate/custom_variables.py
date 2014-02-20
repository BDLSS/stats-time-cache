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
        #self.CONFIG.setup_custom_vars(1) # check count finds stuff
        self.CONNECTION = dbengine.Connection()
        self.CONNECTION.setup(host, username, password, database)
        
    # Count existing data
    def sql_count_customvar_scode(self):
        count = self.CONFIG.FIELD_CUSTOM_VARS_SCODE
        table = self.CONFIG.TABLE_CUSTOM_VARS_STORE 
        return "SELECT COUNT(%s) FROM %s"%(count, table)
    
    def sql_count_customvar_dcode(self):
        count = self.CONFIG.FIELD_CUSTOM_VARS_DCODE
        table = self.CONFIG.TABLE_CUSTOM_VARS_STORE 
        return "SELECT COUNT(%s) FROM %s"%(count, table)
    
    def count_existing(self):
        '''Return the number of custom variables that exist.'''
        scode = self.CONNECTION.fetchone(self.sql_count_customvar_scode())
        logging.info('Count of custom variable: %s'%scode)
        dcode = self.CONNECTION.fetchone(self.sql_count_customvar_dcode())
        logging.info('Count of custom variable: %s'%dcode)
        return scode, dcode
    
    # Lookup custom variables
    def sql_action_lookup(self, action):
        table, key, check, down = self.CONFIG.get_action_look_config()
        return "SELECT %s , %s , %s FROM %s WHERE %s='%s'"%(key, check, down, table, key, action)
    
    def action_lookup(self, action):
        '''Returns data from the key to use as scode and dcode'''
        query = self.sql_action_lookup(action)
        return self.CONNECTION.fetchone(query)
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Populate()
    count = p.count_existing()
    logging.critical(count)
    logging.warn('The above should be empty for a new populate.')
    logging.warn('If not you need to CHECK why!!')
    
    result = p.action_lookup('50') # test the lookup works
    if result:
        if len(result) == 3:
            logging.info(result)
        else:
            logging.warn('Lookup failed.')
    
    
    
    