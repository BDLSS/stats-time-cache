'''A collection of tasks to perform related to Piwik custom variables.'''
import logging
import re

import dbsources
import dbengine

class Populate(object):
    '''Take existing data and populate custom variables.'''
    def __init__(self):
        self.CONFIG = None # tables and fields to use
        self.CONNECTION = None # in this location
        self.setup()
        regexp = '(.*)([0-F]{8}-[0-F]{4}-[0-F]{4}-[0-F]{4}-[0-F]{12})(.*)'
        self.PATTERN_CHECK = re.compile(regexp, re.IGNORECASE)
        
        # These two codes indicate what type of update has occurred
        self.DCODE_IGNORE = 'n' # value to insert when we are not interested
        self.DCODE_VIEW = 'v' # value to insert when it is a view
        
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
        
    def get_action(self, action):
        '''Return details about an action.'''
        result = self.action_lookup(action)
        if not result:
            return False
        
        code = self.action_extract_code(result[1])
        if not code:
            return False
        
        checktype = result[2]
        if checktype == self.CONFIG.ACTION_ISUSEFUL:
            return code, 'view'
        elif checktype == self.CONFIG.ACTION_ISDOWNLOAD:
            return code, 'down'
        else:
            return code, 'other'  
        
    def action_extract_code(self, checkname):
        found = re.search(self.PATTERN_CHECK, checkname)
        if found:
            code = 'uuid:%s'%str(found.group(2)).lower()
            return code
        else:
            return False
            
    # Find data that needs checking to see if custom variables are needed.
    def sql_find_items(self, how='test'):
        table, key, action, site, when, visit, scode, dcode = self.CONFIG.get_store_look_config()
        select = 'SELECT %s , %s , %s , %s , %s , %s , %s FROM %s'%(key,
                        action, site, when, visit, scode, dcode, table) 
        where = ''
        if how == 'test': 
            where = self.where_test()
        return '%s%s'%(select, where)
    
    def where_test(self):
        return ' LIMIT 0, 10'
     
    def find_items_to_populate(self, how='test'):
        query = self.sql_find_items()
        return self.CONNECTION.fetchall(query)

    # Update the store if necessary.
    def sql_update(self, key, scode, dcode):
        table,  fieldkey = self.CONFIG.get_update_store_config()
        update = "UPDATE %s SET "%table
        scode = "%s = '%s' , "%(self.CONFIG.FIELD_CUSTOM_VARS_SCODE, scode)
        dcode = "%s = '%s' "%(self.CONFIG.FIELD_CUSTOM_VARS_DCODE, dcode)
        where = "WHERE %s = %s"%(fieldkey, key)
        return '%s%s%s%s'%(update, scode, dcode, where)
    
    def update_codes(self, key, scode, dcode):
        '''Execute the update of key with scode and dcode.'''
        query = self.sql_update(key, scode, dcode)
        return self.CONNECTION.update(query)
        
    def run_populate(self):
        '''Check the store and update any custom variables needed.'''
        views = 0
        downloads = 0
        others = 0
        for item in self.find_items_to_populate():
            key = item[0]
            action = item[1]
            existing_scode = item[5]
            existing_dcode = item[6]
            
            # dcode controls if this item is updated.
            if existing_dcode == self.DCODE_IGNORE or existing_dcode == self.DCODE_VIEW:
                continue

            # It needs updating, find out what type of update is needed
            # and work out the scodes and dcodes to use.
            useful = self.get_action(action)
            if not useful: # we can ignore it,
                others += 1
                scode = self.DCODE_IGNORE
                dcode = self.DCODE_IGNORE
            else:  # its either a view or download
                new_code = useful[0]
                category = useful[1]
                
                if category == 'view':
                    views += 1
                    if existing_scode:
                        scode = existing_scode 
                    else:
                        scode = new_code
                    dcode = self.DCODE_VIEW
                
                if category == 'down':
                    downloads += 1
                    if existing_dcode:
                        dcode = existing_dcode
                    else:
                        dcode = new_code
                        
                    # Deal with data where the dcode needs changing from known values
                    if dcode == self.DCODE_IGNORE or dcode == self.DCODE_VIEW:
                        dcode = new_code
                        
                    # Deal with archived data that starts off with no scode,
                    if existing_scode:
                        scode = existing_scode
                    else:
                        scode = new_code
                          
            self.update_codes(key, scode, dcode)
            
        return views, downloads, others
            
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
    
    print 'Expect to see    uuid:15b86a5d-21f4-44a3-95bb-b8543d326658'
    print p.get_action('33162') #type 4
    print p.get_action('33257') #view
    print p.get_action('33258') #down
    
    print p.find_items_to_populate()
    print p.run_populate()
    