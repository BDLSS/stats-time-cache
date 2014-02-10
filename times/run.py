'''Run all engines testing the samples.'''
import logging
import os
import time

import engines # how results are obtained
import samples # what results are needed

class Runner(object):
    '''Runs all the available engines.'''
    def __init__(self, saveto, sample_limit=1, pause_between=1):
        '''Prepare to run engines and save report to file specified.'''
        self.SAMPLE_LIMIT = sample_limit
        self.PAUSE_BETWEEN = pause_between
        self.RESULT = list()
        self.DIV1 = '='*50
        self.DIV2 = '-'*50
        self.REPORT_SAVE = saveto
        
    def run_engines(self):
        '''Run all the available engines.'''
        self.save(header=True)

        self.run_engines_single()
        
        self.log('%s\nEnd for report.\n%s\n'%(self.DIV1, self.DIV1))
        self.save()
        
    def run_engines_single(self):
        '''Run engines that can get data with a single request.'''
        singles  = engines.SingleRequest()
        for source in singles.SOURCES:
            logging.info('Running engine: %s'%source) 
            self.log('\n%s\n%s\n'%(source, self.DIV2))
            self.log(self.report_time('Start: '))
            
            singles.setup(source)
            sam = samples.Samples(self.SAMPLE_LIMIT, 1)
            sam.enable(singles.get, source)
            sam.runall()
            sam.save()
            
            self.log(self.report_time('Finish: '))
            self.log('%s\n'%self.DIV2)
            self.log(sam.summary_table())
            self.log('\n%s\n\n'%self.DIV2)
            self.save()
            self.RESULT = list()
            time.sleep(self.PAUSE_BETWEEN)
    
    def report_time(self, prefix=''):
        when = time.strftime('%y-%m-%d at %H:%M:%S', time.gmtime())
        return '%s%s\n'%(prefix, when)
    
    def log(self, message):
        self.RESULT.append(message)
    
    def save(self, header=False):
        '''Save a report of this run to the filepath.'''
        if header:
            fmode= 'w'
            content = '%s\nSummary of tests.\n%s\n'%(self.DIV1, self.DIV1)
            content += '-For each method, the start and finish time is shown.\n'
            content += '-Each sample, the time taken in minutes is first.\n'
            content += '-For a small sample time in seconds is a better measure.\n'
            content += '-Average time to get results for each item in sample.\n'
            content += '-The name of the sample contains the sample size.\n'
            content += '%s\n%s\n'%(self.DIV1,self.report_time('Generated: '))
        else:
            fmode = 'a'
            content = ''
            for report in self.RESULT:
                content += report
        
        with file(self.REPORT_SAVE, fmode) as outfile:
            outfile.write(content)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    e = engines.Engine()
    preload1 = e.get('/results/dv/8b/0b/6cac-e205-41d9-a9f8-f0ca39f6b7eb').read()
    preload2 = e.get('/results/dv/53/2d/3978-9c85-4dc3-a6f7-73b3bd1814f3').read()
    print preload1.strip(), preload2.strip()
    
    report = os.path.join(os.getcwd(),'reports','summary_engines.txt') 
    r = Runner(report)
    r.run_engines()
    