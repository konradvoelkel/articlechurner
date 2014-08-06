"""
ArticleChurner version 0.1-alpha
2014 by Konrad Voelkel
License: public domain
"""

#BUGs:
# when using the userscript to add known uris, old content is removed.

#TODOs even more:
# move to github
# more stats for better feedback
#  want to do full logfile
#  and then extract some stats from the log

from sys import argv
from time import strftime
from random import randint, choice
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cgi import FieldStorage
from mark3.markdown import markdown
from urllib.parse import urlparse, parse_qs
import re
import csv #TODO csv doesn't do unicode; encode UTF-8

CSVQUOT = csv.QUOTE_NONNUMERIC
TIME_FORMAT = "%Y%m%d (%A, %d.%b %y, %H:%M)"
TEMPLATES = ("header","footer","all","archive","single","new","error","index")
formatted_time = lambda : strftime(TIME_FORMAT)

def poprandomrow(table):
    """using third row (integer 0-10) to alter probability:
    0 means never, 10 is highest
    items with 5 are half as likely to be pulled again."""
    table_as_list = list(table) # a generator won't suffice here!
    while(True):
        row = choice(table_as_list)
        if(row["rating"] >= randint(1,10)):
            table_as_list.remove(row)
            return table_as_list, row

def raw_row_to_dict(raw_row):
    return dict(uri=raw_row[0],
                title=raw_row[1],
                rating=int(raw_row[2]),
                notes=raw_row[3],
                mdnotes=markdown(raw_row[3]))

def dict_to_raw_row(row):
    return [row["uri"], row["title"], row["rating"], row["notes"]]

def get_table(filename):
    """returns a reader on an open csv file at filename"""
    return (raw_row_to_dict(raw_row)
            for raw_row in csv.reader(open(filename), quoting=CSVQUOT))

def update_table(filename, uri, title, oldnotes, newnotes, rating):
    # if the url was known, remove old version:
    updatedtable = [dict_to_raw_row(row)
                    for row in get_table(filename) if row["uri"] != uri]
    # add new/updated version:
    if(newnotes == ""):
        notes = oldnotes
    else:
        # add markdown h3 with timestamp (as promised by UI)
        notes = oldnotes + "\n### " + formatted_time() + " ###\n" + newnotes
    updatedtable.append([uri, title, rating, notes])
    csv.writer(open(filename, 'w'), quoting=CSVQUOT).writerows(updatedtable)

def filter_table(filename, condition):
    updatedtable = [dict_to_raw_row(row) for row in get_table(filename) if condition(row)]
    csv.writer(open(filename, 'w'), quoting=CSVQUOT).writerows(updatedtable)

class MyRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.filename = server.filename
        # after the following line, no code gets executed:
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
    
    def write_html_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "private")
        self.end_headers()

    def do_POST(self):
        form = FieldStorage(fp=self.rfile,
                            headers=self.headers,
                            environ={'REQUEST_METHOD':'POST',
                                     'CONTENT_TYPE':self.headers['Content-Type'],
                                     })
        if "/edit/" in self.path or "/rand/" in self.path:
            uri = form["uri"].value
            self.path = "/edit/?uri="+uri
            oldnotes_if_any = form["oldnotes"].value if "oldnotes" in form else ""
            newnotes_if_any = form["newnotes"].value if "newnotes" in form else ""
            update_table(self.filename,
                         uri=uri,
                         title=form["title"].value,
                         oldnotes=oldnotes_if_any,
                         newnotes=newnotes_if_any,
                         rating=form["rating"].value)
        #TODO kill archive function is currently disabled in menu; better replace with bulk edit!
        #elif self.path == "/killarchive/": # row[2]==0 means archive
        #    filter_table(self.filename,
        #                 condition=lambda row:row["rating"]!=0)
        #    self.path = "/"
        elif self.path == "/killsingle/":
            filter_table(self.filename,
                         condition=lambda row:row["uri"]!=form["killuri"].value)
            self.path = "/" #TODO go back to previous (form["returnurl"] hidden)
        else:
            self.path += "/error/"
        self.do_GET()

    def write_template(self, template, substitution={}):
        self.wfile.write(bytes(self.server.template_strings[template] % substitution, 'UTF-8'))

    def do_GET(self):
        if self.path == "/style.css" or self.path == "/favicon.ico":
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.write_html_headers()
            self.write_template("header")
            parsed_query = parse_qs(urlparse(self.path).query)
            if self.path == "/":
                self.write_template("index")
            elif self.path == "/single/":
                table, row = poprandomrow(get_table(self.filename))
                row.update(dict(timestamp=formatted_time()))
                self.write_template("single", substitution=row)
            elif "/edit" in self.path:
                uri = parsed_query.get("uri")
                if(uri):
                    for row in get_table(self.filename):
                        if(uri[0] == row["uri"]):
                            row.update(dict(timestamp=formatted_time()))
                            self.write_template("single", substitution=row)
                else:
                    self.write_template("new",
                                    substitution=dict(timestamp=formatted_time()))
            #elif self.path == "/archive/": #TODO merge into /search/
            #    for row in get_table(self.filename):
            #        if(row["rating"] == 0): # rating==never, thus inactive
            #            self.write_template("archive",
            #                                substitution=row) #TODO doesnt work any longer correctly: notes/mdnotes
            elif "/search" in self.path:
                q = parsed_query.get("q")
                minratings = parsed_query.get("minrating")
                minrating = int(minratings[0]) if minratings else 0
                maxratings = parsed_query.get("maxrating")
                maxrating = int(maxratings[0]) if maxratings else 0
                regex = re.compile(q[0], re.IGNORECASE) if q else re.compile("")
                for row in get_table(self.filename):
                    if(minrating <= row["rating"] <= maxrating):
                        if(regex.search(row["notes"]) or
                           regex.search(row["title"])):
                            self.write_template("all",
                                                substitution=row)
            else:
                self.write_template("error")
            self.write_template("footer")

class MyHTTPServer(HTTPServer):

    def update_template_strings(self):
        for template in TEMPLATES:
            with open("template_"+template+".html") as f:
                self.template_strings[template] = f.read()

    def __init__(self, filename, server_address=('', 8000), RequestHandlerClass=MyRequestHandler):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.filename = filename
        self.template_strings = dict()
        self.update_template_strings()

def main():
    if(len(argv) != 2):
        print("USAGE: python serve-annotator filename.csv")
        return
    script, filename = argv
    MyHTTPServer(filename).serve_forever()

if(__name__ == "__main__"):
    main()
