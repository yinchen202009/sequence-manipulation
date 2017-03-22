# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 14:27:49 2014

@author: RDT
"""

from Bio import SeqIO
import csv
import sys

def get_seqs(seqfile, seq_to_pull, outfile):
    '''Open fasta infile and return iterator of SeqRecords with protein sequences.'''
    records = SeqIO.parse(seqfile, 'fasta')
    seqlist=[]
    for rec in records:
	if seq_to_pull in rec.id:
		seqlist.append(rec)
		print seqlist
        else:
                continue
    
    with open(outfile, 'w') as f:
        SeqIO.write(seqlist, f, 'fasta')


def main():
	assert len(sys.argv) == 3, "usage: python pullseqs_fromtrinity.py <sequences.fasta> <sequence name>"
	infile = sys.argv[1]
	print "infile is", infile
	seq_to_pull = sys.argv[2]
	print "sequence name or keyword is", seq_to_pull
	outfile = infile[:infile.index('.fasta')]+'_'+seq_to_pull+'.fasta'
	get_seqs(infile,seq_to_pull,outfile)
	
main()
