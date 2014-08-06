"""
markdown-to-csv

This script takes a markdown text blob (preserving encoding) and looks for all URLS in this pattern: [title](URL) and outputs a comma-separated values file (excel dialect) with columns URL,title,rating,notes where rating is by default 10.0 and notes is the empty string."""

from sys import argv
import re

url_regex = re.compile(".*\[([^\[]+)\]\(([^\)]+)\).*") # match groups: title, url

def markdowntocsv(textstream):
    parsedstream = ["\"%s\",\"%s\",10.0,\"\"" % (match.group(2), match.group(1)) for match in [url_regex.match(line) for line in textstream] if match]
    return "\n".join(parsedstream)

def main():
    if(len(argv) != 3):
        print("USAGE: python markdown-to-csv infile.md outfile.csv")
        return
    script, infile, outfile = argv
    outstream = open(outfile, 'w')
    instream = open(infile)
    outstream.write(markdowntocsv(instream))
    instream.close
    outstream.close

if(__name__ == "__main__"):
    main()
