'''Run all engines testing the samples.'''
import logging
import os
import time

import engines # how results are obtained
import samples # what results are needed
import sources # for multiple engines

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
        self.REPORT_BY_SAMPLE = dict()
        
    def run_engines(self, testitem=[]):
        '''Run all the available engines.'''
        self.save(header=True)

        # prepare storage for the report by sample
        sam = samples.Samples(self.SAMPLE_LIMIT, 1)
        for sample in sam.SAMPLES:
            self.REPORT_BY_SAMPLE[sample] = list()
        del(sam)
        
        self.run_engines_single(testitem)
        self.single_resultget(testitem)
        self.run_engines_multiple(testitem)
        self.final_result()
    
    def final_result(self):
        '''Finish the results output.'''
        self.RESULT += '%s\nEnd summary.\n%s\n'%(self.DIV1, self.DIV1)
        self.RESULT += '\n%s\nResults by samples.\n%s\n\n'%(self.DIV1, self.DIV1)
        self.RESULT += self.report_samples()
        self.RESULT += '\n%s\nEnd results.\n%s\n'%(self.DIV1, self.DIV1)
        self.save()
        
    def run_engines_single(self, testitem):
        '''Run engines that can get data with a single request.'''
        singles  = engines.SingleRequest()
        for source in singles.SOURCES:
            logging.info('Running engine: %s'%source) 
            self.log('\n%s\n%s\n'%(source, self.DIV2))
            self.log(self.report_time('Start: '))
            
            singles.setup(source, singlecode=testitem)
            sam = samples.Samples(self.SAMPLE_LIMIT, 1)
            sam.enable(singles.get, source)
            sam.runall()
            sam.save()
            
            for sample in sam.SAMPLES: # put samples together
                content = sam.summary_sample(sample, source)
                self.REPORT_BY_SAMPLE[sample].append(content)
            
            self.log(self.report_time('Finish: '))
            self.log('%s\n'%self.DIV2)
            self.log(sam.summary_table())
            self.log('\n%s\n'%self.DIV2)
            self.save()
            self.RESULT = list()
            time.sleep(self.PAUSE_BETWEEN)
            
    def single_resultget(self, testitem):
        '''Do a single customised test using results-get'''
        source = 'results-get'
        host = "HOST"
        singles = engines.SingleRequest()
        singles.setup(source, host, testitem)
        sam = samples.Samples(self.SAMPLE_LIMIT, 1)
        sam.enable(singles.get, source)
        sam.runall()
        sam.save()
        for sample in sam.SAMPLES: # put samples together
            content = sam.summary_sample(sample, source)
            self.REPORT_BY_SAMPLE[sample].append(content)
    
    def multiple_sources(self):
        '''Return a tuple of of which multiple sources to test.'''
        ms = sources.PiwiEngines()
        return ms.get_sources()
        
    def run_engines_multiple(self, testitem):
        '''Run engines that need to get data with a multiple requests.'''
        sources = self.multiple_sources()
        autosort = 10
        for source in sources:
            autosort += 1
            name = source[0]
            token = source[1]
            root = source[2]
            subdir = source[3]
            query = source[4]
            label = '%s_%s'%(name, query)
            
            logging.info('Running engine: %s'%name) 
            self.log('\n%s\n%s\n'%(name, self.DIV2))
            self.log(self.report_time('Start: '))
            
            multi = engines.MultipleRequest()
            multi.setup(token, root, subdir, query=query, singles=testitem)
            sam = samples.Samples(self.SAMPLE_LIMIT, 1)
            
            sam.enable(multi.get, 's%s_%s'%(autosort, label))
            sam.runall()
            sam.save()
            
            for sample in sam.SAMPLES: # put samples together
                content = sam.summary_sample(sample, label)
                self.REPORT_BY_SAMPLE[sample].append(content)
            
            self.log(self.report_time('Finish: '))
            self.log('%s\n'%self.DIV2)
            self.log(sam.summary_table())
            self.log('\n%s\n'%self.DIV2)
            self.save()
            self.RESULT = list()
            time.sleep(self.PAUSE_BETWEEN)
        
    def report_time(self, prefix=''):
        when = time.strftime('%y-%m-%d at %H:%M:%S', time.gmtime())
        return '%s%s\n'%(prefix, when)
    
    def report_samples(self):
        '''Return a string that collates a sample for all test runs.'''
        result = list()
        for sample in self.REPORT_BY_SAMPLE:
            result.append(sample)
            result.append('TMins\tTSecs\tTAverage\tTest run')
            for part in self.REPORT_BY_SAMPLE[sample]:
                result.append(part)
            result.append('')
        return '\n'.join(result)
        
    def log(self, message):
        self.RESULT.append(message)
    
    def save(self, header=False, content=''):
        '''Save a report of this run to the filepath.'''
        if header:
            fmode= 'w'
            content = '%s\nSummary of tests.\n%s\n'%(self.DIV1, self.DIV1)
            content += '-For each method, the start and finish time is shown.\n'
            content += '-Each sample, the time taken in minutes is first.\n'
            content += '-For a small sample time in seconds is a better measure.\n'
            content += '-Average time to get results for each item in sample.\n'
            content += '-The name of the sample contains the sample size.\n'
            content += '%s\n%s'%(self.DIV1,self.report_time('Generated: '))
        else:
            fmode = 'a'
            if not content: 
                for report in self.RESULT:
                    content += report
        
        with file(self.REPORT_SAVE, fmode) as outfile:
            outfile.write(content)

def command_line():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-d', help='Enables debug logging', dest='debug',
                      default=False, action="store_true")
    parser.add_option('-v', help='Enables info logging', dest='info', 
                      default=False, action="store_true")
    (options, unused) = parser.parse_args()
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif options.info:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.warn('Running engines, showing warnings only.')
    
if __name__ == '__main__':
    command_line()    
    e = engines.Engine()
    preload1 = e.get('/results/dv/8b/0b/6cac-e205-41d9-a9f8-f0ca39f6b7eb').read()
    preload2 = e.get('/results/dv/53/2d/3978-9c85-4dc3-a6f7-73b3bd1814f3').read()
    print preload1.strip(), preload2.strip()
    
    report = os.path.join(os.getcwd(),'reports','summary_engines.txt') 
    r = Runner(report, 2)
    r.run_engines('rowan')
    
