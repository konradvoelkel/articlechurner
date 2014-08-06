"""
annotate_randomly

DEPRECATED; use serve_annotator

takes a csv file with four columns like "url","title",rating,"notes"
takes user input to edit a randomly chosen line
writes user input back to the line

csv dialect used: excel
"""

from sys import argv
from random import randint,choice
from time import strftime
import csv #TODO csv doesn't do unicode; encode UTF-8

time_format = "%Y%m%d (%A, %d.%b %y, %H:%M)"

def poprandomrow(table):
    """using third row (integer 0-10) to alter probability:
    0 means never, 10 is highest
    items with 5 are half as likely to be pulled again."""
    while(True):
        row = choice(table)
        if(int(row[2]) >= randint(1,10)):
            table.remove(row)
            return table, row

def poprandomrow_file(filename):
    stream = open(filename)
    table, row = poprandomrow(list(csv.reader(stream, quoting=csv.QUOTE_NONNUMERIC)))
    stream.close
    return table, row

def getuserinput(line):
    print("What about this item:\n\t%s\n\t%s\n\t\t(old rating: %s)%s" % tuple(line))
    newrating = input("\t\tnew rating (0-10): ")
    print("\nAnnotation:")
    notesectionheader = "### "+strftime(time_format)+" ###\n"
    newnotes = input(notesectionheader)
    return [line[0],line[1],newrating, "%s\n%s%s" % (line[3],notesectionheader,newnotes)]

def writetofile(table, filename):
    stream = open(filename, 'w')
    csv.writer(stream, quoting=csv.QUOTE_NONNUMERIC).writerows(table)
    stream.close

def single_transaction(filename):
    table, row = poprandomrow_file(filename)
    table.append(getuserinput(row))
    writetofile(table, filename)

def main():
    if(len(argv) != 2):
        print("USAGE: python annotate_randomly filename.csv")
        return
    script, filename = argv
    single_transaction(filename)

if(__name__ == "__main__"):
    main()
