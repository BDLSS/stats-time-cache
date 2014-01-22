# This script converts existing date from a previous version of Piwik
# to a new version with an option to convert certain data.
import os
import logging

DIR_ROOT = os.getcwd()
DIR_OLD = os.path.join(DIR_ROOT, 'olddata')
DIR_NEW = os.path.join(DIR_ROOT, 'newdata')

def run():
    logging.debug(DIR_OLD)
    logging.debug(DIR_NEW)
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run()