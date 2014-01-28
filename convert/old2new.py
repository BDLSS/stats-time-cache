# This script converts existing date from a previous version of Piwik
# to a new version with an option to convert certain data.
import os
import logging
import csv
import re #To detect UUIDs in urls
import pickle

# If the logging level is set to debug, it is possible
# to enable large quantities of output whilst the data is being
# converted rather than just using that provided by reports afterwards.
DETAILED_DEBUG_LINKS = False
DETAILED_DEBUG_VISITS = False

class Converter(object):
    '''Control the conversion process.'''
    def __init__(self):
        self.DIR_ROOT = os.getcwd()
        self.DIR_OLD = os.path.join(self.DIR_ROOT, 'olddata')
        self.DIR_NEW = os.path.join(self.DIR_ROOT, 'newdata')
        self.FILE_ACTIONS = 'actions.tsv'
        self.FILE_LINKS = 'links.tsv'
        self.FILE_VISITS = 'visits.tsv'
        self.DELIMITER = "\t"

        #The classes that will do the conversion when called.
        self.ACTIONS = Actions()
        self.LINKS = Links()
        self.VISITS = Visits()
        
    def _process_file_with_function(self, filepath, function,
                                    limit=None, headstore=None):
        '''Process the lines in contained in filepath with function.'''
        if not limit: # Enable part processing of file
            limit = 2000000
        logging.info('Processing file: %s'%filepath)
        logging.info('Using function: %s'%function)
        logging.info('Number of lines limited to: %s'%limit)
        converted = 0 # lines that converted okay
        failed = 0 # attempts at conversion that failed
        skipped = 0 # lines that caused CSV errors
        with open(filepath, 'rb') as infile:
            #lines = csv.DictReader(infile, delimiter=self.DELIMITER)
            lines = csv.reader(infile, delimiter=self.DELIMITER)
            header = lines.next() # assume data has a header row
            if headstore:
                headstore(header)
            # Cannot use "for line in lines:" because of binary output
            # in column 2 raises an error. Wrapping it in a try block
            # stops processing of further lines. Hence this:
            while True:
                try:
                    if converted == limit:
                        break
                    line = lines.next()
                    if function(line):
                        converted += 1
                    else:
                        failed += 1
                except csv.Error:
                    self.check_line_error(line)
                    skipped += 1
                except StopIteration:
                    break
        logging.info('Number of lines converted: %s'%converted)
        logging.info('Number of lines that failed to convert: %s'%failed)
        logging.info('Number lines skipped: %s'%skipped)
        if skipped > 20:
            logging.warn('Skipped lines were greater than 20.')
    
    def check_line_error(self, line):
        pass
        #logging.debug('WARNING, the following line was skipped.')
        #logging.debug(line)
        #TODO: Check why lines cause a CSV error. Binary field 
        
    def process_actions(self):
        logging.info('Processing actions.')
        # Setup file paths
        filepath = os.path.join(self.DIR_OLD, self.FILE_ACTIONS)
        outfile = os.path.join(self.DIR_NEW, self.FILE_ACTIONS)
        pickfile = os.path.join(self.DIR_NEW, '%s.pickle'%self.FILE_ACTIONS)
        
        # Process the actions or use the cached codes instead.
        if os.path.exists(pickfile):
            logging.critical('Using pickled codes rather then regenerating.')
            logging.critical('Saved conversion will NOT be updated.')
            self.ACTIONS.CODES = pickle.load(open(pickfile, 'rb'))
        else:            
            # Process the actions.
            function = self.ACTIONS.process_line
            self._process_file_with_function(filepath, function)
            self.ACTIONS.report() 
            self.save_converted(self.ACTIONS, outfile)
            self.ACTIONS.pickle_codes(pickfile)
    
    def process_links(self):
        logging.info('Processing links.')
        filepath = os.path.join(self.DIR_OLD, self.FILE_LINKS)
        function = self.LINKS.process_line
        self.LINKS.enable_action_lookup(self.ACTIONS.CODES)
        self._process_file_with_function(filepath, function)
        self.LINKS.report()
        outfile = os.path.join(self.DIR_NEW, self.FILE_LINKS) 
        self.save_converted(self.LINKS, outfile)

    def process_visits(self):
        logging.info('Processing visits')
        fpath = os.path.join(self.DIR_OLD, self.FILE_VISITS)
        fun = self.VISITS.process_line
        hstore = self.VISITS.enable_compare
        self._process_file_with_function(fpath, fun, headstore=hstore)
        self.VISITS.report()
        outfile = os.path.join(self.DIR_NEW, self.FILE_VISITS) 
        self.save_converted(self.VISITS, outfile)
        
    def save_converted(self, data_source, filepath):
        '''Save the contents of data source to file path.'''
        logging.info('Saving converted file to: %s'%filepath)
        outfile = open(filepath, 'wb')
        for data in data_source.DATA:
            line = "\t".join(data)
            outfile.write('%s\n'%line)
        outfile.close()
        
    def run_all(self):
        logging.debug(self.DIR_OLD)
        logging.debug(self.DIR_NEW)
        self.process_actions()
        self.process_links()
        self.process_visits()
        
class Actions(object):
    def __init__(self):
        self.DATA = list() # raw data to be saved
        self.CODES = dict() # codes to use for custom variables
        self.CODES_FOUND = 0
        self.LINES_WITHOUT_CODES = 0
        regexp = '(.*)(uuid:[0-F]{8}-[0-F]{4}-[0-F]{4}-[0-F]{4}-[0-F]{12})(.*)'
        self.PATTERN = re.compile(regexp, re.IGNORECASE)
        
    def process_line(self, line):
        self.DATA.append(line)
        link_lookup_id = line[0] #key field referenced from links
        check = line[1] #field that contains code for custom vars
        
        found = re.search(self.PATTERN, check)
        if not found:
            self.LINES_WITHOUT_CODES += 1
        else:
            self.CODES_FOUND += 1
            code = str(found.group(2)).lower()
            self.CODES[link_lookup_id] = code
        return True
    
    def report(self):
        logging.info('Codes extracted: %s'%self.CODES_FOUND)
        logging.info('Lines without codes %s:'%self.LINES_WITHOUT_CODES)
        
    def pickle_codes(self, filepath):
        # Pickle codes so to speed up test runs.
        logging.info('Pickling codes to: %s'%filepath)
        pickle.dump(self.CODES, open(filepath, 'wb'))

class Links(object):
    '''Process data from table: log_link_visit_action '''
    def __init__(self):
        self.LOOKUP_CODES = dict() # Used to find codes when enabled.
        self.DATA = list() # Converted data.
        self.LINE_LEN_EXPECTED = 20 # number of expected fields
        self.LINE_LEN_FAULTS = list() # store faulty lines for checking
        
    def enable_action_lookup(self, codes):
        '''Dictionary of actions to lookup codes to insert.'''
        self.LOOKUP_CODES = codes
        
    def look_up_code(self, code):
        '''Find the code for this action or'''
        if not self.LOOKUP_CODES:
            return 'CODE>>%s<<CODE'%code
        try:
            return '%s'%self.LOOKUP_CODES[code]
        except KeyError:
            return 'nc' #no code
    
    def get_id(self, line):
        '''Check line matches expected patterns.'''
        if len(line) <> self.LINE_LEN_EXPECTED:
            self.LINE_LEN_FAULTS.append(line)
            return False
        else:
            return line[5] #don't put this in a try block
            
    def process_line(self, line):
        #Find the custom variable and insert into current line
        action_id = self.get_id(line)
        if not action_id:
            return False
        custom_var_code = 11
        line[custom_var_code] = self.look_up_code(action_id)
        
        # Add new columns required into the current line.
        # Field names come from table: piwik_log_link_visit_action 
        index_idaction_name_ref = 8 
        # Need to insert after the above field.
        insert_index = index_idaction_name_ref+1
        # Enable human check before and after the insert
        if DETAILED_DEBUG_LINKS:
            logging.debug('before=%s'%line[index_idaction_name_ref:])
        line.insert(insert_index, 'NULL') #idaction_event_action 
        line.insert(insert_index, 'NULL') #idaction_event_category
        if DETAILED_DEBUG_LINKS:
            logging.debug('after=%s'%line[index_idaction_name_ref:])
        # Note idaction_event_category ends up before the other.
        
        self.DATA.append(line)
        return True
    
    def report(self):
        if self.LOOKUP_CODES:
            logging.info('Code lookup was enabled.')
            nc = 'Number of codes available for lookup was: %s'%len(self.LOOKUP_CODES)
            logging.info(nc)
        else:
            logging.critical('Code lookup disabled, TEST codes used.')
        
        lenfau = len(self.LINE_LEN_FAULTS)
        if lenfau:
            logging.warn("Input lines with unexpected counts: %s"%lenfau)
            for line in self.LINE_LEN_FAULTS:
                logging.debug(line)

class Visits(object):
    '''Process data from table: log_visit '''
    def __init__(self):
        self.DATA = list() # Converted data.
        
        # The table log_visit has a lot of fields, so to confirm
        # conversion is okay slices are used. This splits a visit
        # into a number of chunks so a visual check is easier when
        # comparing before and after.  Given the number of visits
        # this visual check is not possible on every one. To enable
        # this the check on each chunk can vary. If the result does
        # not match expected patterns it logs the this.
        self.SLICES = (#(bmin, bmax, amin, amax, check)
                  (0,6,0,9,3), # three fields get moved here
                  (6,10,9,13,'='), # starts with 2 action times
                  (10,14,13,17,'='), # contains 4 visit numbers
                  (14,17,17,21,1), # a new field appears here
                  (17,21,21,25,'='), # contains 4 referrer fields
                  (21,25,25,29,'='), # contains 4 config fields
                  (25,36,29,40,'='), # starts with config screen res
                  (36,43,40,47,'='), # contains 7 location fields
                  (43,47,47,47,'none'), # four field are moved from here 
                  (47,57,48,60,1), # one field gets moved here after 10 custom fields
                  )
        
        # A second check occurs that does not require the
        # above slices to be correct. It looks for exact
        # values of certain list indexes before and after
        # the conversion. The easiest to spot visually is
        # the location provider the others are often 0.
        self.CHECK_MOVES = ((43,58, 'location_provider'), # ac.uk
                 (44,6, 'visitor_days_since_last'), # 0
                 (45,7, 'visitor_days_since_order'), # 0
                 (46,8, 'visitor_days_since_first'), # 0
                 )
        
        # Keep a record of any issues that occur during processing.
        self.FIELD_ISSUES = list() # while converting a line
        self.COMPARE_ISSUES = list() # during conversion checks
        self.MOVE_ISSUES = list() # that exact values change location
        
    def enable_compare(self, header):
        '''List of fields to use when comparing lines.'''
        self.FIELDS = header
        
    def compare(self, line, content):
        '''Compare line before to the content after to confirm okay.'''
        if DETAILED_DEBUG_VISITS:
            logging.debug('Comparing visits before and after conversion. '+'=='*25)
            logging.debug('All fields: %s'%self.FIELDS) 
        
        issues = [] # save issues with this line for debug
        for s in self.SLICES:
            # Extract output for slices before and after conversion
            bmin = s[0]
            bmax = s[1]
            before = line[bmin:bmax]
            lenB = len(before)
            after =  content[s[2]:s[3]]  
            lenA = len(after)
            if DETAILED_DEBUG_VISITS:
                logging.debug('Fields: %s'%self.FIELDS[bmin:bmax])
                logging.debug('Before: %s'%before)
                logging.debug('After: %s'%after)
            
            # Confirm the output matches expected values or save issues 
            check = s[4] # vary the check depending expected results
            if check == '=': # no change
                okay = lenB == lenA
            elif check == 'none': # removals
                okay = lenA == 0
            else: # additions
                okay = lenB+check == lenA
            if not okay:  # logs 4 notes per item
                issues.append('idvisit=%s'%line[0])
                issues.append('slice=%s'%str(s))
                issues.append('before=%s'%before)
                issues.append('after=%s'%after)
        
        # Confirm movement is as expected without using slices. The
        # values taken from before and after the move should match.
        for move in self.CHECK_MOVES:
            m_before = line[move[0]]
            m_after = content[move[1]]
            if m_before <> m_after: # logs 3 notes per item
                field = move[2]
                self.MOVE_ISSUES.append('idvisit=%s'%line[0])
                self.MOVE_ISSUES.append('%s before=%s'%(field, m_before))
                self.MOVE_ISSUES.append('%s after=%s'%(field, m_after))
                
        # Confirm the whole line is okay or provide feedback for issues.
        if issues:
            self.COMPARE_ISSUES.extend(issues)
            return False
        else:
            return True
         
    def process_line(self, line):
        '''Process a line representing a visit.'''
        # There are 4 existing fields that need moving and 1 new one.
        try:
            before = line[:] # take a copy to compare since we alter line
            content = line[:6]
            location = 44
            content.append(line.pop(location)) # visitor_days_since_last
            content.append(line.pop(location)) # visitor_days_since_order
            content.append(line.pop(location)) # visitor_days_since_first
            content.extend(line[6:14])
            content.append('NEW visit_total_events')
            content.extend(line[14:63])
            content.append(line.pop(43)) # location_provider
            self.compare(before, content)
            self.DATA.append(content)
            return True
        except IndexError:
            entry = 'fcount=%s line=%s'%(len(line), line)
            self.FIELD_ISSUES.append(entry)
            return False
            
    def report(self):
        # Report issues that stopped line being processes.
        reports = (#(list of issues, type of issue, number of notes per issue
                   (self.FIELD_ISSUES, 'Field', 1),
                   (self.COMPARE_ISSUES, 'Compare', 4),
                   (self.MOVE_ISSUES, 'Move', 3),
                   )
        
        for report in reports:
            issue = report[1]
            found = len(report[0])/report[2]
            logging.warn('%s issues occurred.'%issue)
            logging.info('%s issues found: %s'%(issue, found))
            for item in report[0]:
                logging.debug(item)
             
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, filename='result_old2new.log')
    c = Converter()
    c.run_all()