"""Organizes and parses configuration files


USAGE
=======

myconfigs=fattyconfig.fattyConfig("filename.cnf")


Set log
--------------------------------
myconfigs.set_log()


file_in_dir() -- Get file within a directory specified in [dir] section of config
------------

ifile=myconfigs.file_in_dir("dir_config_opt",newest=1)


filename for new file in <config_opt> within the "dir" section
------------
ofile=myconfigs.new_filename_in_dir("dir_config_opt",basename="")



arbitrary config
------------
Use the configparser object
opt=myconfigs.config.get("section","option")

"""

import csv
import configparser
import os.path

import logging

from jjfattypy import fattyio,fattylog


#this is used to separate values within a config that takes multiple values
LISTSPLITTER=","

class fattyConfig:
	
    def __init__(self,config_file,encoding=None):
        """custom config option, includes configparser object as self.config"""

        #check if config file exists
        if not os.path.isfile(config_file):
			#if it doesnt, make a new one
            fattyio.display("No config file found at path %s"%config_file)
            while not os.path.isfile(config_file):
                config_file=fattyio.prompt_file(os.path.dirname(config_file),os.path.basename(config_file),nocheck=1)

        self.filename=config_file
		
        self.config=configparser.ConfigParser()
        for enc in [encoding,"utf8","sjis","cp932","utf16"]:
            try:
                self.config.read(self.filename,encoding=enc)
            except UnicodeDecodeError:
                if not enc==None:
                    fattyio.display("Unable to load config file with encoding %s"%enc)
            else:
                break

    def set_log(self,verbose=0,basename=""):
        """open a logfile"""
        log_dir=self.config.get("dir","logs") or self.config.get("dir","log")
        fattylog.setlog(basename,verbose)        
        
    def file_in_dir(self,dir_config_opt,newest=True):
        """return file from within the directory specified by <dir_config_opt>, within the [dir] section of the config file"""
        idir=self.config.get("dir",dir_config_opt)
        newest_file=fattyio.newest_file_in(idir)
        if newest:
            return newest_file
        else:
            return fattyio.prompt_file(idir,os.path.basename(newest_file))

    def new_filename_in_dir(self,dir_config_opt,basename="",append_date=0):
        """make a new filename in the directory specified by the given dir_config_opt"""
        odir=self.config.get("dir",dir_config_opt)
        
        if append_date or basename=="":
            basename=fattyio.date_filename(basename)

        full_path=os.path.join(odir,basename)
        return full_path
	
    def list_from_config(self,section,config,separator=","):
        """return a list from a config option having <separator>-separated values, 
        <separator> is "," by default"""
        list_str=self.config.get(section,config)
        list=list_str.split(separator)
        return list

    def read_mapping_file(self,idir_config_opt,config_section="",ifile_config_section="",ifile_config_opt="",base_dir="",newest=False,force=False,header=False,delimiter="\t",input_filename=""):
        """return a mapping dictionary matching key->column number, based on an input mapping dir
        """        
        full_path=""
        if input_filename and os.path.isfile(input_filename):
            full_path=input_filename
        
        if config_section=="":
            config_section="dir"
        
        mapping_file_dir=self.config.get(config_section,idir_config_opt)
        #if the mapping_file_dir is not actually path, try combining it with a base directory
        logging.info("Attemping to load mapping data")

        if not os.path.isdir(mapping_file_dir) and not base_dir=="" and not full_path:

            base_dir=self.config.get("dir","basedir")
            if os.path.isdir(os.path.join(base_dir,mapping_file_dir)):
                mapping_file_dir=os.path.join(base_dir,mapping_file_dir)
                logging.info("Found mapping dir: %s"%mapping_file_dir)
            else:
                logging.error("Unable to find mapping directory %s"%os.path.join(base_dir,mapping_file_dir))
                return None

        if os.path.isdir(mapping_file_dir):
            if os.path.isfile(os.path.join(mapping_file_dir,input_filename)):
                full_path=os.path.join(mapping_file_dir,input_filename)
            else:
                basename=self.config.get(ifile_config_section,ifile_config_opt)
                if os.path.isfile(os.path.join(mapping_file_dir,basename)):
                    full_path=os.path.join(mapping_file_dir,basename)
                else:
                    logging.info("Unable to find file %s in directory %s"%(basename,mapping_file_dir))
                    fattyio.display("Unable to find file %s in directory %s"%(basename,mapping_file_dir))
                    default_file=""
                    if newest or force:
                        default_file=newest_file_in(mapping_file_dir)                
                    full_path=fattyio.prompt_file(mapping_file_dir,default_file,nocheck=force,file_title="column mapping file")

        else:
            logging.error("Unable to find the directory of the mapping file: %s"%mapping_file_dir)
            return None
        mapping={}
        ##Now, read the file
        rownum=0
        logging.info("Full path to mapping file: %s"%full_path)        
        mapping=parse_mapping_file(full_path,header=header)
            
        return mapping
                
def parse_mapping_file(ifile,header=False,delimiter="\t"):
    """parse a given mapping file and return the output"""
    mapping={}
    
    if not os.path.isfile(ifile):
        logging.error("Given input file %s is not a file, unable to produce mapping data")
        return None
    else:
        csv_dets=fattyio.fatty_csv_dets(ifile)        
        with open(csv_dets["filename"],encoding=csv_dets["encoding"]) as ifh:
            icsv=csv.reader(ifh,delimiter=csv_dets["delimiter"])
            rownum=0
            for row in icsv:
                if rownum==0 and header:
                    header=False
                    continue
                if len(row)<2:
                    rownum+=1
                    continue
                if row[1].strip() != "":
                    keys=row[1].split(",")
                    for k in keys:
                        if not k in mapping:
                            mapping[k]=[]
                        
                        mapping[k].append({"colnum": rownum,"order":None})
                        try:
                            mapping[k][len(mapping[k])-1]["order"]=int(row[2])
                        except IndexError or ValueError:
                            logging.debug("No order information found for this row in mapping file")
                rownum+=1
    return mapping


def fatty_configs():
    """return fattyConfig object based on a default configuration file"""

    configs=fattyConfig(os.path.join(os.path.dirname(__file__),"..",".jjfattypy"))    
    
    return configs
