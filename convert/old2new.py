# This script converts existing date from a previous version of Piwik
# to a new version with an option to convert certain data.
import os
import logging
import csv
import re #To detect UUIDs in urls

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

    def _process_file_with_function(self, filepath, function, limit=None):
        '''Process the lines in contained in filepath with function.'''
        if not limit: # Enable part processing of file
            limit = 1000000000
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
            logging.debug('Header: %s'%header)
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
        filepath = os.path.join(self.DIR_OLD, self.FILE_ACTIONS)
        function = self.ACTIONS.process_line
        self._process_file_with_function(filepath, function)
        self.ACTIONS.report()
        outfile = os.path.join(self.DIR_NEW, '%s.tsv'%self.FILE_ACTIONS) 
        self.ACTIONS.save(outfile)
    
    def process_links(self):
        logging.info('Processing links.')
        filepath = os.path.join(self.DIR_OLD, self.FILE_LINKS)
        function = self.LINKS.process_line
        self.LINKS.enable_action_lookup(self.ACTIONS.CODES)
        self._process_file_with_function(filepath, function)
        self.LINKS.report()
        outfile = os.path.join(self.DIR_NEW, '%s.tsv'%self.FILE_LINKS) 
        self.LINKS.save(outfile)

    def run_all(self):
        logging.debug(self.DIR_OLD)
        logging.debug(self.DIR_NEW)
        self.process_actions()
        self.process_links()
        
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
        
    def save(self, filepath):
        logging.info('Saving actions to: %s'%filepath)

class Links(object):
    '''Process data from table: log_link_visit_action '''
    def __init__(self):
        self.LOOKUP_CODES = dict() # Used to find codes when enabled.
        self.DATA = list() # Converted data.
        
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
    
    def process_line(self, line):
        #Find the custom variable and insert into current line
        action_id = line[5]
        custom_var_code = 11
        line[custom_var_code] = self.look_up_code(action_id)
        
        # Add new columns required into the current line.
        # Field names come from table: piwik_log_link_visit_action 
        index_idaction_name_ref = 8 
        # Need to insert after the above field.
        insert_index = index_idaction_name_ref+1
        # Enable human check before and after the insert
        logging.debug(line[index_idaction_name_ref:])
        line.insert(insert_index, 'NULL') #idaction_event_action 
        line.insert(insert_index, 'NULL') #idaction_event_category
        logging.debug(line[index_idaction_name_ref:])
        # Note idaction_event_category ends up before the other.
        
        self.DATA.append(line)
        return True
    
    def report(self):
        if self.LOOKUP_CODES:
            logging.info('Code lookup was enabled.')
            nc = 'Number of codes available for lookup: %s'%len(self.LOOKUP_CODES)
            logging.info(nc)
        else:
            logging.critical('Code lookup disabled, test codes where used.')
    
    def save(self, filepath):
        logging.info('Saving actions to: %s'%filepath)
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c = Converter()
    c.run_all()