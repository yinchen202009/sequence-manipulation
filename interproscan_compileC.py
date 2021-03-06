
#!/usr/bin/env python

# import pylauncher
import sys
import os
import csv
import time
from Bio import SeqIO



## global variables ##
input_file=sys.argv[1]
start_date=(time.strftime("%d/%m/%Y"))
date_formatted=time.strftime("%Y-%m-%d")
start_time=(time.strftime("%H:%M:%S"))
name=input_file.strip('.txt')+'_logfile.txt'
logfile=open(name,'w')

def shorten_filename(input_file,new_ending):
	"""This function takes two positional arguments:
		1. the input file, with a full path
		2. the new ending for the file
	It returns a tuple including the new file without the path that starts with today's 
	date and with the new ending, as well as the shortened version of the filename."""
	
	fileshort=(input_file.split('/')[-1]).split('.')[0]
	return (date_formatted+"_"+fileshort+new_ending,fileshort)
	
	
def parsefile(input_file,sep='\t'):
    """This function takes one positional argument, the input file, and one optional argument,
    the file separator. The default is tab-delimited but can be specified for other types. The
    function parses the input file into a list of lists and returns this as a list."""
    
    start = time.clock()
    with open(input_file,'rU') as f:
        reader=csv.reader(f,delimiter=sep)
        d=list(reader)
	print >>logfile,"%s was parsed in %fs." %(input_file,(time.clock() - start))
# 	print >>logfile, "### Parsed file is:\n",d,"\n"
    return d
    

# input_file='/Users/RDT/Documents/Research/NextGenPilot_Harvard/annotations/testfile.txt'
# parsed_input_file=parsefile(input_file)
# (seqlist,length)=makelist(parsed_input_file,input_file,0)
# dictionary=rowfinder(seqlist,parsed_input_file,4)

def pullsequences(perframe,trinity_file):
	"""This function takes two positional arguments:
		1. the dict_perframe created by rowfinder() containing sequence info and all identifiers per frame
		2. the trinity file that corresponds to the analysis
	It returns a list of sequences that match the list from the dictionary and edits the
	descriptions so that they contain GO and protein identifiers listed by ORF number & frame length.
	"""
	
	start= time.clock()
	with open(perframe,'r') as f:
		dict_perframe=f.read()
	fastaList=[]
	wanted=[k[0] for k in dict_perframe.keys()]
	wanted=list(set(wanted))
# 	print  >>logfile, "### Sequences to be pulled are:\n", wanted,"\n"
	for seq in SeqIO.parse(open(trinity_file, 'rU'),'fasta'): #find the sequence in the right file
		if seq.id in wanted: # if the sequence matches one in our dictionary
			for item in dict_perframe: # then find the dict entry
				if seq.id in item[0]: # by matching sequence ID to the first tuple item
					seq.description = seq.description+"\tFrame_"+item[1]+"_Len_"+item[2]+"_Identifiers=["+",".join(dict_perframe[item])+']'
			fastaList.append(seq) #copy to a list
# 	print >>logfile, "### New sequence list is:\n",fastaList,"\n"
	print >>logfile,"Sequences pulled in %fs." %(time.clock() - start)
	return fastaList
	
	
def parse_blastX(blast_output,columns):
	"""This function takes two positional arguments:
		1. an outfmt6 file from blastX
		2. the columns that you want to pull from the outfmt6 file that you want to add to the annotations
	This function is particular to the specific columns it was written for because it parses them in a certain
	way to improve readability. It would have to be rewritten for other columns. It returns a dictionary 
	with sequences as keys and blast annotations as values. 
	"""
	
	#subset outfmt6 file and splice strings
	start = time.clock()
	blasts=parsefile(blast_output)
	subset=[]
	for line in blasts:
		geneinfo=line[columns[2]]
		geneinfo_short=geneinfo[:geneinfo.index('PE=')].strip() #cut before PE and SV values
		combined_ID=(geneinfo_short.split(' '))[0] # save first geneinfo item as combined_ID
		geneinfo_short=' '.join((geneinfo_short.split(' '))[1:]) #split by spaces, then remove combined_ID, then rejoin with spaces
		gene_desc=geneinfo_short[:geneinfo_short.index('OS=')].strip() # subset the gene description, which comes after combined_ID and ends before OS_ID
		OS_ID=geneinfo_short[geneinfo_short.index('OS='):].strip() # subset organism name
		OS_genus=OS_ID[OS_ID.index('=')+1:OS_ID.index(' ')] # subset genus
		OS_species=OS_ID[OS_ID.index(' '):] # subset specific epithet
		if 'GN=' in geneinfo: # if there is a gene name already in the output
			geneID=geneinfo_short[geneinfo_short.index('GN=')+3:].strip() # save as a separate geneID
			OS_species=OS_species[:OS_species.index('GN=')].strip() # and strip GN from the OS
			GN_info='GN_existed' # make a note where this information is from
		else: # if gene name not in GN= NCBI space, use the gene identifier from the species specific notation
			geneID=geneinfo[geneinfo.index('|')+1:geneinfo.index('_')] # then select a portion of the first geneinfo
			while '|' in geneID: # remove all information (separated by |) except the gene identifier
				geneID=geneID[geneID.index('|')+1:]
			GN_info='GN_added' # make a note where this information is from
		
		#add seqID, e-value, gene description, organism genus, organism species, geneID, geneID origin, and combinedID
		addendum=[line[columns[0]],line[columns[1]],gene_desc,OS_genus,OS_species, geneID, GN_info,combined_ID] 
		subset.append(addendum)
	
	# save list as dictionary with sequence IDs as keys and blast information as values
	blast_dict={}
	for item in subset:
		blast_dict[item[0]]=item[1:]
# 	print >>logfile, "### Subset of blast output to be added is:\n",blast_dict
	print >>logfile,"Blast dictionary created in %fs" %(time.clock() - start)
	return blast_dict
		
		
def add_blast_info(blast_dict,annotated_seqs):
	"""This function takes two positional arguments:
		1. the blast dictionary from parse_blastX()
		2. the list of GO annotated sequences from pullsequences()
	The function outputs an updated version of the annotated sequences that includes the 
	blast information.
	"""
	start = time.clock()
	updated_seqs=[]
	for seq in annotated_seqs: # find the sequence in the right file
		for item in blast_dict:
			if seq.id == item:
				seq.description = seq.description+"\tBlast_Hit=["+",".join(blast_dict[item])+']'# 
				updated_seqs.append(seq) #copy to a list
	print >>logfile,"Blast information added to sequence file in %fs." %(time.clock() - start)
	return updated_seqs
			
def print_BGOlist(perseq_dict,blast_dict):
	"""This function takes two positional arguments:
		1. the dictionary with GO identifiers per sequence
		2. the dictionary with blast information per sequence
	It prints a tab-delimited file that combines these dictionaries. Number of cells will
	vary depending on the number of identifiers from the GO file. The number of cells used
	for the blast output will be the same for all sequences. Reported sequence length is only
	for one of the frames.
	"""

	start= time.clock()
	with open(perseq_dict, 'r') as f:
		GO_dict=f.read()
	output_file,short_name=shorten_filename(input_file,'_BLASTnGOlist.txt')
	with open(output_file, 'w') as f:
		for k in blast_dict:
			for g in GO_dict:
				if k == g:
					assert k == g, "sequences do not match!! %s != %s" %(k,g)
					f.write("%s\t%s\t%s\t%s\n" %(short_name,k,'\t'.join(blast_dict[k]),'\t'.join(GO_dict[g])))
	print >>logfile,"Huge text file printed in %fs." %(time.clock() - start)


def print_output(fastaList):
	"""This function takes one argument, the doubly-annotated sequence list. It prints it
	to a fasta file.
	"""
	
	start= time.clock()
	output_file,short_name=shorten_filename(input_file,'_sequences.fasta')
	with open(output_file, 'w') as f:
		SeqIO.write(fastaList, f, "fasta") #export to a file
	print >>logfile,"Printed final sequence file in %fs." %(time.clock() - start)
	

def main():
	perframe_dict,short_name=shorten_filename(input_file,'_perframe.txt')
	perseq_dict,short_name=shorten_filename(input_file,'_perseq.txt')
	sequences=pullsequences(perframe_dict,sys.argv[2])
	blast_results=parse_blastX(sys.argv[3],[0,10,13])
	blast_sequences=add_blast_info(blast_results,sequences)
	print_BGOlist(perseq_dict,blast_results)
	print_output(blast_sequences)

	end_date=(time.strftime("%d/%m/%Y"))
	end_time=(time.strftime("%H:%M:%S"))

	print >>logfile,"Start date and time was %s %s" %(start_date, start_time)
	print >>logfile,"End date and time was %s %s" %(end_date, end_time)
	logfile.close()

main()
