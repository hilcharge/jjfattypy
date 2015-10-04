##
#generic python modules
import csv
import fattyio
import pprint
import os
import sys,getopt
import datetime
import logging
import glob
from subprocess import Popen,PIPE
import shlex
#can be used regardless of system
from jjfattypy import fattylog,fattyconfig,fattydb

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

    def set_outputfile(self,outputfile,filetype="txt"):
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
            self.outputdir=self.inputdir     
            self.outputfile=os.path.join(outputdir,"combo"+datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")+"."+filetype)
            self.outfiletype="txt"
        else:
            self.outputfile=outputfile
        logging.info("Using output file: %s"%self.outputfile)
        fattyio.display("Using output file: %s"%self.outputfile)

    def set_recursive(self,recursive):
        self.recursive=recursive
        if self.recursive:
            fattyio.display("Recursive NOT currently implemented")
            logging.error("User wanted to perform recursive combination, not currently implemented")
    def set_filetypes(self,filetypes):
        #set filetypes to be combined
        #default is csv
        self.filetypes=[]
        if len(filetypes)==0:
            self.filetypes.extend(["xls","xlsx","xlsm"])
        else:
            self.filetypes=filetypes                
                    
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
            logdir=fattylog.logdir()
            date_logdir=fattyio.make_date_folder_in(logdir)
            fulllog=date_logdir+"//"+logfilename
        else:            
            date_logdir=fattyio.make_date_folder_in(logdir)
            fulllog=date_logdir+"//"+logfilename
            
        #start the log
        
        fattylog.setlog(fulllog,verbose)
 
        logging.info("Script: %s"% __file__)
            
    def do_stuff(self):
        #here is where the main actions of the program take place
        available_files=[]
        logging.info("Getting available files in input folder %s"%self.inputdir)        
        logging.info("filetypes: %s"%",".join(self.filetypes))
        available_files=[]
        for thistype in self.filetypes:
            globstr=os.path.join(self.inputdir,"*.%s"%thistype)
            logging.debug("Glob str: %s"%globstr)
            available_files.extend(glob.glob(globstr))
            logging.debug("Available files: %s","/n"+"\n".join(available_files))
        logging.info("Found %i files"%len(available_files))        
        vbs_base='cscript.exe "%s"'%(os.path.join(os.getenv("HOME_BIN"),"Excel2tsv.vbs"))
        for file in available_files:
            vbs_call='%s "%s"'%(vbs_base,file)
            logging.info("Executing visual basic call")
            logging.debug(vbs_call)
            output,error=Popen(shlex.split(vbs_call),stdout=PIPE,stderr=PIPE).communicate()
            logging.info("Output: "+str(output))
            if error:
                logging.info("Error: "+str(error))

        tsv_files=glob.glob(os.path.join(self.inputdir,"*.txt",))        
        logging.info("Opening output file %s"%self.outputfile)
        self.ofh=open(self.outputfile,"w")        
        fattyio.combine_files(tsv_files,self.outputfile,self.separator)        

        return 0        

    # def combine_files(self,picked_files):
    #     #combine the files
    #     filecount=0
    #     ocsv=csv.writer(self.ofh,lineterminator="\n",delimiter=self.separator,encoding="utf16")
    #     for ifile in picked_files:
    #         rownum=0
    #         ifh=open(ifile)
    #         icsv=csv.reader(ifh)
    #         for row in icsv:
    #             #if its the first row of the non-first file, skip it
    #             if rownum==0 and filecount!=0:
    #                 rownum+=1
    #                 continue
    #             #otherwise write the row
    #             ocsv.writerow(row)
    #             rownum+=1
    #         filecount +=1
    #         logging.info("Finished file %s"%ifile)            
    #         ifh.close()
    #     logging.info("Finished all files, wrote to outputfile %s" % self.outputfile)
    #     self.ofh.close()                                    
    #     return 0

def main(argv):
    # default base dir for ami-angel combined system is based on environment variable
    #try getting args, or else print proper usage
    usage_str="""backup-db.py [-v] -u <user> -p <password> -i <input_dir> -o <output_filename> 
    -v: verbose
    -h: help
    -c,--configfile: specify configuration file
    -o, --output-file: specify-output-filename
    -l,--logfile: specify logfile
    -d,--inputdir: specify input dir for files (default is current working directory)
    -a,--allfiles: all files in the given directory
    -t,--filetypes: specify filetypes, default csv (separated by commes), e.g. --filetypes="csv"
    -r, --recursive: Recursively combine files (NOT CURRENTLY IMPLEMENTED)
    -s, --separator: specify separator i.e. comma or tab
    """
    verbose=0
    logfile=""
    myscript=MyScript()
    configfile=""
    inputdir=""
    outputfile=""
    allfiles=0
    filetypes=[]
    recursive=0
    separator=""
    try:
        opts,args=getopt.getopt(argv,"hvaRt:i:o:c:l:s:",["filetypes=","input-dir=","output-file","configfile=","logfile=","separator="])
    except getopt.GetoptError:
        fattyio.display(usage_str)
        sys.exit(2)

    for opt,arg in opts:
        if opt== "-h":
            fattyio.display(usage_str)
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
