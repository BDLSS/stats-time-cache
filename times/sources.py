'''Configure sources to run against.'''

class PiwiEngines():
    def __init__(self):
        self.SOURCES = list()
    
    def add(self, name, token, ipaddress, subdir=None, query='last5years'):
        '''Add named engine with token and IP address.'''
        if subdir == 'root':
            subdir = ''
        elif not subdir: # assume subdir matches name
            subdir = name
        if query not in ['last5years', 'last12months', 'ac1year']:
            query = 'last5years'
        source = (name, token, ipaddress, subdir, query)
        self.SOURCES.append(source)

    def enable_all(self):
        self.enable_orastats()
        self.enable_localvm()
                
    def enable_orastats(self):
        ipaddress = 'THE IP'
        token = 'YOUR TOKEN'
        self.add('orastats', token, ipaddress, 'root') 

    def enable_localvm(self):
        ipaddress = 'THE IP'
        token = 'YOUR TOKEN'
        self.add('pi_noarchives', token, ipaddress)
        self.add('pi_archives', token, ipaddress)
        self.add('pi_bigarchives', token, ipaddress)
        self.add('pi_indexed', token, ipaddress)
        self.add('pi_indexed', token, ipaddress, query='last12months')
        self.add('pi_indexed', token, ipaddress, query='ac1year')

    def get_sources(self):
        self.enable_all()
        return self.SOURCES
        
    def __str__(self):
        return str(self.SOURCES)
    
if __name__ == "__main__":
    pe = PiwiEngines()
    pe.enable_all()
    print pe