"""used for setting up log parameters
Standard usage: 
import fattylog
logdir=fattylog.logdir()
verbose=1
filename=os.path.join("logdir","mytestlog.log")
fattylog.setlog(filename,verbose)
"""

import logging
import os
from jjfattypy import fattyio
import sys



LEVELS={'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'critical':logging.CRITICAL
}

def setlog(fn,verbose,ft='%(asctime)s [%(levelname)s] %(message)s'):
    mode=0
    logging.getLogger("").handlers=[]
    if verbose:
        mode=LEVELS.get("debug")
        fattyio.display("Logging mode: %i"%mode)        
    else:
        mode=LEVELS.get("info")    
    if os.path.isdir(os.path.dirname(fn)):
        fattyio.display("Found log folder %s"%os.path.dirname(fn))
        logging.basicConfig(filename=fn,filemode="w",level=mode,format=ft)
        logging.info("Begin logging")
        logging.critical("Testing critical")
        logging.warning("Testing warning")
        logging.debug("Testing debug")
        if not os.path.exists(fn):
            logging.warning("No log file created, checking default folder")
            logdir=logdir()
            if os.path.exists(logdir):
                fn=os.path.join(logdir,os.path.basename(fn))
                logging.basicConfig(filename=fn,filemode="w",level=mode,format=ft)
                logging.info("Begin logging")
                logging.critical("Testing critical")
                logging.warning("Testing warning")
                logging.debug("Testing debug")
                if not os.path.exists(fn):
                    logging.critical("No log file created, checking default folder")
                    return 0
                    sys.exit()        
    else:
        fattyio.display("No log dir exists %s, exiting"%fn)
        sys.exit()

def logdir(folder=""):
    if folder == "" or not os.path.isdir(folder):
        try:
            folder=os.getenv("MY_LOG_DIR")
        except:
            fattyio.display("Unable to determine log directory logfile, therefore unable to execute script")
            sys.exit()
        else:
            fattyio.display("Log directory: %s"% folder)
    return folder

