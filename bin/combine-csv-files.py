##
#generic python modules
import csv
import kanio
import pprint
import os
import sys,getopt
import datetime
import logging
import glob
#can be used regardless of system
from kansha import kanlog,kanconfig,kandb

CONFIG_FOLDER="conf_NISSAN_TRIAL"

class MyScript():

    def set_allfiles(self,allfiles):
        #true if all files in directory should be combined
        self.allfiles=allfiles
    def set_inputdir(self,direc):
        if direc == "":
            self.inputdir=os.getcwd()
        else:
            self.inputdir=direc        
        if not os.path.isdir(self.inputdir):
            logging.critical("Given input path %s not a directory, exiting"%self.inputdir)
            sys.exit()
    def set_separator(self,separator):
        if separator=="":
            self.separator=","
        elif separator in ["tab","\t"]:
            self.separator="\t"
        else:
            logging.error("Unable to use specified separator, using default comma instead")
            self.separator=","

    def set_outputfile(self,outputfile):
        #set output file and output directory
        self.outputfile=""
        if outputfile=="":
            outputdir=os.path.join(self.inputdir,"output")            
            if not os.path.isdir(outputdir):
                logging.info("Making output directory %s"%outputdir)
                os.makedirs(outputdir) 
                if not os.path.exists(outputdir):
                    logging.critical("Unable to make output dir %s, exiting"%outputdir)
                    sys.exit()
            self.outputdir=outputdir     
            self.outputfile=os.path.join(outputdir,"combo"+datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")+"."+self.filetypes[0])
        else:
            self.outputfile=outputfile
        logging.info("Using output file: %s"%self.outputfile)
        kanio.display("Using output file: %s"%self.outputfile)

    def set_recursive(self,recursive):
        self.recursive=recursive
        if self.recursive:
            kanio.display("Recursive NOT currently implemented")
            logging.error("User wanted to perform recursive combination, not currently implemented")
    def set_filetypes(self,filetypes):
        #set filetypes to be combined
        #default is csv
        self.filetypes=[]
        if len(filetypes)==0:
            self.filetypes.append("csv")
        else:
            self.filetypes=filetypes                
    def set_configs(self,config_filename=""):
        #This sets the config file for the script
        if config_filename != "":
            self.configs=kanconfig.kanConfig(config_filename)       
            self.hasconfig=1
        else:
            self.hasconfig=0        
                    
    def set_log(self,logdir,verbose=0,logfilename=""):        
        #Sets the log file for the script
        #after setting this, you can use the standard logging lib
        #i.e. logging.info("This is a message")
        #If no log filename was given, create one using the script name and date time. This is safest, try not to add your own logfile
        if logfilename=="":
            logfilename=os.path.basename(__file__)+"-"+datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")+".log"
        fulllog=""
        logdir=logdir.replace(r"\\","//")
        print("log dir:",logdir)
        #if no log directory was given, make one using the standard
        if logdir=="":
            logdir=kanlog.logdir()
            date_logdir=kanio.make_date_folder_in(logdir)
            fulllog=date_logdir+"//"+logfilename
        else:            
            date_logdir=kanio.make_date_folder_in(logdir)
            fulllog=date_logdir+"//"+logfilename
            
        #start the log
        
        kanlog.setlog(fulllog,verbose)
 
        logging.info("Script: %s"% __file__)
            
    def do_stuff(self):
        #here is where the main actions of the program take place
        available_files=[]
        logging.info("Getting available files in input folder %s"%self.inputdir)        
        logging.info("filetypes: %s"%",".join(self.filetypes))
        if len(self.filetypes)==1:
            glob_str=os.path.join(self.inputdir,"*.%s"%self.filetypes[0])
            logging.debug("Glob str: %s"%glob_str)
            available_files=glob.glob(glob_str)
            print("globber:",glob_str)
            print("avail_files",available_files)
        else:
            available_files=glob.glob(os.path.join(self.inputdir,"*.{%s}"%",".join(filetypes)))
        logging.info("Found %i files"%len(available_files))        
        logging.info("Opening output file %s"%self.outputfile)
        self.ofh=open(self.outputfile,"w")
        picked_files=[]
        if not self.allfiles:
            logging.info("Prompting user to select files")
            picked_files=kanio.prompt_for_many_from_list(available_files,"input files")        
        else:
            picked_files=list(available_files)
        
        kanio.combine_files(picked_files,self.outputfile,self.separator)        

        return 0        

def main(argv):
    # default base dir for ami-angel combined system is based on environment variable
    #try getting args, or else print proper usage
    usage_str="""backup-db.py [-v] -u <user> -p <password> -i <input_dir> -o <output_filename> 
    -v: verbose
    -h: help
    -o, --output-file: specify-output-filename
    -l,--logfile: specify logfile
    -d,--inputdir: specify input dir for files (default is current working directory)
    -a,--allfiles: all files in the given directory
    -t,--filetypes: specify filetypes, default csv (separated by commes), e.g. --filetypes="csv"
    -r, --recursive: Recursively combine files (NOT CURRENTLY IMPLEMENTED)
    -s, --separator: specify separator of input files i.e. comma or tab
    """
    verbose=0
    logfile=""
    myscript=MyScript()
    inputdir=""
    outputfile=""
    allfiles=0
    filetypes=[]
    recursive=0
    separator=""
    try:
        opts,args=getopt.getopt(argv,"hvart:i:o:c:l:s:",["filetypes=","input-dir=","output-file","configfile=","logfile=","separator="])
    except getopt.GetoptError:
        kanio.display(usage_str)
        sys.exit(2)

    for opt,arg in opts:
        if opt== "-h":
            kanio.display(usage_str)
            sys.exit()        
        elif opt == "-v":
            verbose=1
        elif opt in ("-a","--allfiles"):
            allfiles=1
        elif opt=="-i":
            inputdir=arg        
        elif opt in ("-o","--output-file"):
            outputfile=arg
        elif opt in ("-i","--input-dir"):
            inputdir=arg
        elif opt in ("-c","--configfile"):
            configfile=arg            
        elif opt in ("-l","--logfile"):
            logfile=arg 
        elif opt in ("-t","--filetypes"):
            filetypes.extend(arg.split(","))            
        elif opt in ("-r","--recursive"):
            recursive=1
        elif opt in ("-s","--output-separator"):
            separator=arg
    
    myscript.set_log("",verbose,logfile)
    myscript.set_allfiles(allfiles)
    myscript.set_inputdir(inputdir)
    myscript.set_separator(separator)
    myscript.set_filetypes(filetypes)
    myscript.set_outputfile(outputfile)
    myscript.set_recursive(recursive)

    #your log is now set and you should be ready to go, to use logging throughout your     
    logging.info("I am still working")
    #    logging.info("Obtaining input and output directory for dictionary creation")

    myscript.do_stuff()
    

if __name__=="__main__":
    main(sys.argv[1:])
