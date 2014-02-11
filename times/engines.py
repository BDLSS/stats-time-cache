'''Engines for testing the samples.'''
import logging
import time # to time it
import socket # to capture error
import httplib  # to fetch data
#httplib.HTTPConnection.debuglevel = 1
import urllib # so we can encode urls
import json

import samples # enable the running of samples
import tokens # so calls to Piwik API will work

class EngineError(Exception):
    pass

class Engine(object):
    '''Connection to an engine via an HTTP connection.'''
    def __init__(self, host='orastats.bodleian.ox.ac.uk', persist=True):
        '''Connect to host with a persistent connection by default.'''
        self.HOST = host
        self.PERSIST = persist
        self.CONNECTION = None # This does the fetching.
        self.HEADERS = {'User-agent' : 'ora_timestats'}
        if not persist: 
            self.HEADERS['Connection'] = 'close'
        
    def connect(self, host=None):
        '''Start a HTTP connection to host or use engine default.'''
        if not host:
            host = self.HOST
        if not self.CONNECTION:
            self.CONNECTION = httplib.HTTPConnection(host, timeout=10)
            logging.debug('New connection: %s'%host)

    def get(self, suburl):
        '''Return response to a get request for suburl from the host.'''
        if not self.CONNECTION:
            self.connect()
        try :
            self.CONNECTION.request('GET', suburl, headers=self.HEADERS)
            return self.CONNECTION.getresponse()
        except (socket.error, httplib.CannotSendRequest, httplib.BadStatusLine):
            raise EngineError
        
    def close(self):
        '''Close the HTTP connection if required.'''
        if not self.PERSIST and self.CONNECTION:
            logging.debug('Closing connection')
            self.CONNECTION.close()
            
class SingleRequest(object):
    '''Engine to collect results where a single URL can be used.'''
    def __init__(self):
        '''Start the engine so it is ready for setup.'''
        self.URL_ROOT = None
        self.URL_SOURCE = None # This will point to a method for calling
        self.SOURCES = ['or-static', 'or-vdown', 'or-indexed']
        self.ENGINE = Engine()
    
    def setup(self, source, root=None):
        '''Source controls how the URL is combined with root url.'''
        if not root:
            root = 'orastats.bodleian.ox.ac.uk'
        self.URL_ROOT = root
        self.ENGINE.connect(self.URL_ROOT)
        
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
        return '/results/dv/%s/%s/%s'%(d1,d2,fname)
    
    def url_vdown(self, item):
        return '/results/vdown.php?scode=%s'%item
        
    def url_indexed(self, item):
        return '/results/vdown_act.php?scode=%s'%item
        
    def get(self, scode):
        '''Get results for scode timing how long it takes.'''
        address = self.URL_SOURCE(scode)
        
        istart = time.time()
        try:
            indata = self.ENGINE.get(address)
            content = indata.read()
        except EngineError:
            content = ''
        iend = time.time()
        timetaken = iend-istart
        self.ENGINE.close() # ignored if connection is persistent
        
        content = self.extract(content)
        return content, timetaken
    
    def extract(self, content):
        '''Check the content for the information expected.'''
        if not content:
            return 'e0;e0'
        if len(content) > 20:
            if '404 Not Found' in content:
                return 'n0;n0'
        else:
            return str(content).strip()

class MultipleRequest(object):
    '''Engine to collect results where multiple URLs are needed used.'''
    def __init__(self):
        self.URL_ROOT = ''
        self.ENGINE = Engine()
        self.URL_SUBDIR = '' # enables usage if Piwik not in root dir
        self.URL_ITEMS = list() # store base urls items come from
        self.TOKEN = '' # Token need to query API
        self.URL_ITEM = '' # The type of item to check for
    
    def setup(self, token, root=None, subdir='', item='THESIS01'):
        self.TOKEN = token
        if not root:
            root = 'orastats.bodleian.ox.ac.uk'
        if subdir: # This will enable query of multiple Piwik installs
            self.URL_SUBDIR = subdir # on the same server.
        self.URL_ITEMS = ('http://ora.ox.ac.uk/objects/', 'http://ora.ouls.ox.ac.uk/objects/')
        self.URL_ITEM = '/datastreams/%s'%item # count downloads
        self.URL_ROOT = root
        self.ENGINE.connect(self.URL_ROOT)

    def shared_params(self):
        params = dict()
        params['module']='API'
        params['token_auth']= self.TOKEN
        params['idSite']=1
        params['period']='year'
        params['date']='today'
        params['format']='json'
        return params
            
    def url_views(self, item):
        if self.URL_SUBDIR:
            return '/%s/views: %s'%(self.URL_SUBDIR, item)
        else:
            return '/views: %s'%item

    def url_downs(self, item, baseurl):
        '''Return a URL to get download stats for item at itemsurl.'''
        params = self.shared_params()        
        params['method']='Actions.getDownload'
        
        item = '%s%s%s'%(baseurl, item, self.URL_ITEM )
        #item = 'http://ora.ox.ac.uk/objects/uuid%3A15b86a5d-21f4-44a3-95bb-b8543d326658/datastreams/THESIS01'
        #params['downloadUrl'] = item   # Don't use this. Since Piwik
        #returns empty. It looks urlencode of "http://" is causing issues.
        
        encoded = urllib.urlencode(params)
        if self.URL_SUBDIR: # Piwik install not at root of website.
            return '/%s/index.php?%s&downloadUrl=%s'%(self.URL_SUBDIR, encoded, item)
        else:
            return '/index.php?%s&downloadUrl=%s'%(encoded, item)

    def fetch(self, webpage):
        '''Return time taken and data from webpage on a host engine.'''
        istart = time.time()
        try:
            indata = self.ENGINE.get(webpage)
            data = indata.read()
        except EngineError:
            data = ''
        iend = time.time()
        timetaken = iend-istart
        return timetaken, data
    
    def get_downloads(self, scode):
        '''Return time taken to get total downloads for scode.'''
        totaldownloads = 100
        totaltime = 0.0
        for baseurl in self.URL_ITEMS:
            url = self.url_downs(scode, baseurl)
            timetaken, data = self.fetch(url)
            totaltime += timetaken
            try:
                results =  json.loads(data)[0] # indexerror
                totaldownloads += results['nb_visits'] #keyerror
            except (IndexError, KeyError):
                logging.debug('No downloads: %s'%scode)
                logging.debug('URL: %s'%url)
                logging.debug('Data, time taken: %s'%timetaken)
                logging.debug(str(data))                
        return totaldownloads, totaltime
    
    def get_views(self, scode):
        '''Return time taken to get total view for scode.'''
        views = self.url_views(scode)
        return len(views), 0.0
        
    def get(self, scode):
        '''Get results for scode, timing all needed requests.'''
        views, viewtime = self.get_views(scode)
        downloads, downtime = self.get_downloads(scode)
        content = '%s;%s'%(views, downloads)
        return content, viewtime+downtime
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    TEST_SINGLE = False
    TEST_MULTIPLE = True
    
    # Check URL read is working.
    e = Engine()
    preload1 = e.get('/results/dv/8b/0b/6cac-e205-41d9-a9f8-f0ca39f6b7eb').read()
    preload2 = e.get('/results/dv/53/2d/3978-9c85-4dc3-a6f7-73b3bd1814f3').read()
    print preload1.strip(), preload2.strip()
    
    if TEST_SINGLE:
        # Setup the engine to use.
        s = SingleRequest() # start is so we can access list of sources
        source = s.SOURCES[0] # test only the first one
        s.setup(source)

        # Run samples against engine.
        sam = samples.Samples(1, 1)
        sam.enable(s.get, source)
        sam.runall()
        print sam.result()
    
    if TEST_MULTIPLE:
        # Test engine that needs to do multiple requests.
        m =  MultipleRequest()
        m.setup(tokens.orastats)
        sam2 = samples.Samples(1, 1)
        sam2.enable(m.get, 'multitest')
        sam2.runall()
        print sam2.result()
        