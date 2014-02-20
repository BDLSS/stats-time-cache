'''A collection of tasks to perform related to Piwik custom variables.'''
import logging

import dbsources
import dbengine

class Populate(object):
    '''Take existing data and populate custom variables.'''
    def __init__(self):
        self.FIELD_TO_POPULATE = '' # field to put data
        self.CONNECTION = None # in this location
    
    def config_variable(self, number=5, usevalue=True):
        '''Set custom variable to use the numbered value column.'''
        if number not in range (1, 6): # Piwik has upto 5 custom vars
            number = 5
        cat = 'v' # we will use the "value column of this custom var"
        if not usevalue:
            cat = 'k' # but you can use the key column instead.
        self.FIELD_TO_POPULATE = 'custom_var_%s%s'%(cat, number)
        logging.debug('Using field: %s'%self.FIELD_TO_POPULATE)
        
    def setup(self):
        '''Setup the connection to the system being populated.'''
        source = dbsources.ReadWriteDB()
        source.setup_source1()
        host, username, password, database = source.get_settings()
        self.CONNECTION = dbengine.Connection()
        self.CONNECTION.setup(host, username, password, database)
        
    def sql_count_customvar(self):
        return "SELECT COUNT(%s) FROM piwik_log_link_visit_action"%self.FIELD_TO_POPULATE
    
    def count_existing(self):
        '''Return the number of custom variables that exist.'''
        answer = self.CONNECTION.fetchone(self.sql_count_customvar())
        logging.info('Count of custom variable: %s'%answer)
        return answer
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    p = Populate()
    p.config_variable()
    p.setup()
    existing = p.count_existing()
    if existing:
        logging.critical('Data EXISTS in custom variables to populate.')
        logging.warn('If this is a new populate you need to check WHY.')
        
    