'''Run a selection of engines testing the samples.'''
import logging
import urllib2 # to fetch data
import time # to time it
import os

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
        self.REPORTS= list()
        self.DIV1 = '='*50
        self.DIV2 = '-'*50
        
    def run_engines(self):
        '''Run all the available engines.'''
        self.run_engines_single()
    
    def report_time(self, prefix=''):
        when = time.strftime('%y-%m-%d at %H:%M:%S', time.gmtime())
        return '%s%s\n'%(prefix, when)
    
    def log(self, message):
        self.REPORTS.append(message)
        
    def run_engines_single(self):
        '''Run engines that can get data with a single request.'''
        singles  = SingleRequest()
        for source in singles.SOURCES:
            logging.info('Running engine: %s'%source) 
            self.log('\n%s\n%s\n'%(source, self.DIV2))
            self.log(self.report_time('Start: '))
            
            singles.setup(source)
            sam = samples.Samples()
            sam.enable(singles.get, source)
            sam.runall()
            sam.save()
            
            self.log(self.report_time('Finish: '))
            self.log('%s\n'%self.DIV2)
            self.log(sam.summary_table())
            self.log('\n%s\n\n'%self.DIV2)
    
    def save(self, filepath):
        '''Save a report of this run to the filepath.'''
        d = self.DIV1
        content = '%s\nSummary of tests.\n%s\n'%(d, d)
        content += '%s\n'%self.report_time('Generated: ')
        for report in self.REPORTS:
            content += report
        content += '%s\nEnd for report.\n%s\n'%(d, d)
        with file(filepath, 'w') as outfile:
            outfile.write(content)
        
if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    report = os.path.join(os.getcwd(),'reports','summary_engines.txt') 
    r = Runner()
    r.run_engines()
    r.save(report)
    