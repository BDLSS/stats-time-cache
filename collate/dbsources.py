'''Database sources of data to look at.'''

class ReadWriteDB(object):
    def __init__(self):
        self.READ_ENABLED = False
        self.WRITE_ENABLED = False
        
        self.READ_HOST = ''
        self.READ_USERNAME = ''
        self.READ_PASSWORD = ''
        self.WRITE_HOST = ''
        self.WRITE_USERNAME = ''
        self.WRITE_PASSWORD = ''
        
    def _enable(self, host, user, password):
        '''Configure DB to use same settings for reading and writing.'''
        self._enable_read(host, user, password)
        self._enable_write(host, user, password)
        
    def _enable_read(self, host, user, password):
        self.READ_HOST = host
        self.READ_USERNAME = user
        self.READ_PASSWORD = password
        self.READ_ENABLED = True
        
    def _enable_write(self, host, user, password):
        self.WRITE_HOST = host
        self.WRITE_USERNAME = user
        self.WRITE_PASSWORD = password
        self.WRITE_ENABLED = True
        
    def setup_source1(self):
        '''Use source 1 for the database connection.'''
        self._enable('testhost', 'testuser', 'testpassword')
    
if __name__ == "__main__":
    rw = ReadWriteDB()
    rw.setup_source1()
    ats = dir(rw)        
    for item in sorted(ats):
        if not str(item).startswith('_'):
            print item, '=', getattr(rw, item)
        
        