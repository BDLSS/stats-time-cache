'''Load and runs a set of samples to see how long they take.'''
import logging
import glob
import time
import random
import os

QUICK_MAX = 0.5 # maximum time quick engine can pretend to take

class SampleSet(object):
    '''Set of items to get results from engine and gather timings.'''
    def __init__(self):
        self.ITEMS = dict() # store the items
        self.ENGINE = None # engine to query, a method or function
        self.NAME = None # name of sample
        self.KRESULT = 'result' # keys to store data
        self.KTOOK = 'took'
        self.TIME_TOTAL = 0
        self.TIME_AVERAGE = 0
        self.TIME_MINUTES = 0
        
    def test_engine_quick(self, scode):
        '''Get results for scode using random values.'''
        timetaken = random.uniform(0.1, QUICK_MAX)
        views = random.randint(101,199)
        downs = random.randint(1,99)
        return '%s;%s'%(views,downs), timetaken

    def load(self, lines):
        '''Extract items to query from lines.'''
        for scode in lines:
            cleaned = str(scode).strip()
            self.ITEMS[cleaned] = {self.KRESULT:str(), self.KTOOK:0}
    
    def enable(self, engine=None, name=None):
        '''Setup engine to query and give it a name.'''
        if not engine:
            engine = self.test_engine_quick
        if not name:
            name = 'quick'
        self.ENGINE = engine
        self.NAME = name
        
    def run(self):
        '''Run items against the engine getting results and time taken.'''
        logging.debug('Using engine: %s'%self.ENGINE)
        for item in self.ITEMS:
            istart = time.time()
            self.ITEMS[item][self.KRESULT], etime = self.ENGINE(item)
            iend = time.time()
            if etime: # enable engine to return time taken
                time_taken = etime
            else:
                time_taken = iend-istart
            self.ITEMS[item][self.KTOOK] = time_taken 
        self.calc_times()
        logging.info('Total time: %s'%self.TIME_TOTAL)
        logging.info('Average time: %s'%self.TIME_AVERAGE)

    def calc_times(self):
        '''Return the total and average times for this set.'''
        totaltime = 0.0
        for item in self.ITEMS:
            totaltime += self.ITEMS[item][self.KTOOK]
        avetime = totaltime/len(self.ITEMS)
        self.TIME_TOTAL = '%.1f'%(totaltime)
        self.TIME_AVERAGE = '%.3f'%avetime
        self.TIME_MINUTES = '%.1f'%(totaltime/60)

    def result(self):
        '''Return a summary of results.'''
        answer = list()
        numitems = len(self.ITEMS)
        answer.append('Number of items: %s'%numitems) 
        answer.append('Total time taken: %s'%self.TIME_TOTAL)
        answer.append('Average time taken: %s'%self.TIME_AVERAGE)
        answer.append('Minutes taken: %s'%self.TIME_MINUTES)
        return '\n'.join(answer)
                
    def save(self, fname):
        '''Save results to fname (name of set gets appended).'''
        content = list()
        content.append('Result\tTime\tItem')
        for item in self.ITEMS:
            result = self.ITEMS[item][self.KRESULT]
            time = '%.3f'%self.ITEMS[item][self.KTOOK]
            content.append('%s\t%s\t%s'%(result, time, item))
        total, avg = self.TIME_TOTAL, self.TIME_AVERAGE
        content.append('%s\t%s\tTimes, total and average'%(total, avg))
        
        lines = '\n'.join(content)
        fname = '%s-%s.tsv'%(fname, self.NAME)
        with file(fname, 'w') as savefile:
            savefile.writelines(lines)
        logging.info('Saved to: %s'%fname)
        
    def __str__(self):
        return self.result()
        
class Samples(object):
    '''Set of sample to run.'''
    def __init__(self, sample_limit=100, pause_between=5):
        self.SAMPLE_LIMIT = sample_limit # limit number of samples
        self.PAUSE_BETWEEN = pause_between # seconds between samples
        self.SAMPLES = dict() # store for samples
        self.OUTDIR = self.output_dir() # location to save results
        self.SAMDIR = 'batches'
        self.SAMEXT = '.csv'
        self.NAME = None # name of the set of samples
        self.load()
        
    def output_dir(self):
        '''Return the location the report should be output to.'''
        outdir = os.path.join(os.getcwd(),'reports')
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir
    
    def load(self, nameroot=None):
        '''Prepare all samples for processing.'''
        if not nameroot:
            nameroot = '*%s'%self.SAMEXT
        pattern = os.path.join(self.SAMDIR, nameroot)
        samples = glob.glob(pattern) 
        for sample in sorted(samples): 
            self.SAMPLES[sample] = SampleSet()
            with file(sample) as infile:
                lines = infile.readlines()
            self.SAMPLES[sample].load(lines)
            self.SAMPLE_LIMIT -= 1
            if not self.SAMPLE_LIMIT:
                break
        logging.info('Samples to process: %s '%len(self.SAMPLES))
                
    def enable(self, engine=None, name=None):
        '''Enable the engines and names for all samples.'''
        logging.info('Engine enabled: %s'%engine)
        self.NAME = name
        for sample in self.SAMPLES:
            self.SAMPLES[sample].enable(engine, name)
    
    def runall(self):
        '''Run all the samples against the engines and save results.'''
        for sample in sorted(self.SAMPLES):
            logging.info('Doing: %s'%sample)             
            self.SAMPLES[sample].run()
            # need to stop results being in the folder with samples
            name = sample.replace('%s/'%self.SAMDIR, '')
            name = name.replace(self.SAMEXT, '')
            fname = os.path.join(self.OUTDIR, name)
            self.SAMPLES[sample].save(fname)
            if self.PAUSE_BETWEEN:
                time.sleep(self.PAUSE_BETWEEN)
    
    def result(self):
        '''Return a summary of all samples.'''
        answer = list()
        num = len(self.SAMPLES)
        answer.append('='*50)
        answer.append('Summary of samples')
        answer.append('='*50)
        answer.append('Number of samples: %s'%num)           
        for sample in sorted(self.SAMPLES):
            answer.append('Sample: %s'%sample)
            answer.append('-'*50)
            answer.append(str(self.SAMPLES[sample]))
            answer.append('-'*50)
        answer.append('Summary of samples, finished.')
        answer.append('='*50)
        return '\n'.join(answer)
    
    def summary_table(self):
        answer = list()
        answer.append('TMins\tTSecs\tTAverage\tSample')
        for sample in sorted(self.SAMPLES):
            answer.append(self.summary_sample(sample))
        return '\n'.join(answer)
    
    def summary_sample(self, sample, altname=''):
        t = self.SAMPLES[sample].TIME_TOTAL
        a = self.SAMPLES[sample].TIME_AVERAGE
        m = self.SAMPLES[sample].TIME_MINUTES
        if altname: # make it so last column content can vary
            sample = altname
        return '%s\t%s\t%s\t%s'%(m, t, a, sample)
        
    def save(self):
        '''Save a summary of results for all samples.'''
        if not self.NAME:
            self.NAME = 'quick'
        fname = os.path.join(self.OUTDIR,'summary-%s.tsv'%self.NAME)
        with file(fname, 'w') as outfile:
            outfile.write(self.summary_table())
            
    def __str__(self):
        return self.result()
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    number_to_test = 5
    seconds_between = 0.1
    s = Samples(number_to_test, seconds_between)
    s.enable() # this will use internal test engine
    s.runall()
    print s
    print s.summary_table()
    s.save()
