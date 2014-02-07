'''Run a selection of engines testing the samples.'''
import logging
import urllib2 # to fetch data
import time # to time it

import samples # enable the running of samples

class SingleRequest(object):
    '''Engine to collect results where a single URL can be used.'''
    def __init__(self):
        '''Start the engine so it is ready for setup.'''
        self.URL_ROOT = None
        self.URL_SOURCE = None # This will point to a method for calling
        self.SOURCES = ['or-static', 'or-vdown', 'or-indexed']
    
    def setup(self, source, root=None):
        '''Source controls how the URL is combined with root url.'''
        if not root:
            root = 'http://orastats.bodleian.ox.ac.uk/results/'
        self.URL_ROOT = root
        if source not in self.SOURCES:
            raise ValueError
        if source == 'or-static':
            self.URL_SOURCE = self.url_static
        elif source == 'or-vdown':
            self.URL_SOURCE = self.url_vdown
        elif source == 'or-indexed':
            self.URL_SOURCE = self.url_indexed
    
    def url_static(self, item):
        '''Return the URL pattern for fetching data.'''
        d1 = item[5:7] # skip 'uuid:' and get first 2 chars 
        d2 = item[7:9] # directory level 2 is the next 2 chars
        fname = item[9:] # the filename is the rest of the uuid
        sub = 'dv/%s/%s/%s'%(d1,d2,fname)
        staturl = '%s%s'%(self.URL_ROOT,sub)
        return staturl
    
    def url_vdown(self, item):
        url = '%svdown.php?scode=%s'%(self.URL_ROOT, item)
        return url
        
    def url_indexed(self, item):
        url = '%svdown_act.php?scode=%s'%(self.URL_ROOT, item)
        return url
        
    def get(self, scode):
        '''Get results for scode timing how long it takes.'''
        address = self.URL_SOURCE(scode)
        istart = time.time()
        try:
            indata = urllib2.urlopen(address, timeout=5.0)
            viewsdownloads = str(indata.read()).strip()
            indata.close()
        except urllib2.HTTPError:
            viewsdownloads = '0;0'
        iend = time.time()
        timetaken = iend-istart
        return viewsdownloads, timetaken
    
    
class Runner(object):
    '''Runs all the available engines.'''
    def __init__(self):
        self.run_engines()
        
    def run_engines(self):
        '''Run all the available engines.'''
        self.run_engines_single()
    
    def run_engines_single(self):
        '''Run engines that can get data with a single request.'''
        singles  = SingleRequest()
        for source in singles.SOURCES:
            logging.info('Running engine: %s'%source)
            singles.setup(source)
            sam = samples.Samples()
            sam.enable(singles.get, source)
            sam.runall()
            sam.save()
        
if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    r = Runner()
    