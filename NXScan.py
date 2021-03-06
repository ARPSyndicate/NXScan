#!/usr/bin/python3

import sys
import os
import optparse
import concurrent.futures
from collections import defaultdict
import xml.etree.ElementTree as ET

BLUE='\033[94m'
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CLEAR='\x1b[0m'

print(BLUE + "NXScan[1.2] by ARPSyndicate" + CLEAR)
print(YELLOW + "fast port scanning with fancy output" + CLEAR)

if len(sys.argv)<2:
    print(RED + "[!] ./NXScan --help" + CLEAR)
    sys.exit()

else:
    parser = optparse.OptionParser()
    parser.add_option('-l', '--list', action="store", dest="list", help="list of targets to enumerate/scan")
    parser.add_option('-v', '--verbose', action="store_true", dest="verbose", help="enable logging", default=False)
    parser.add_option('-T', '--template', action="store", dest="template", help="path to XSL template [default= ./nmap-bootstrap.xsl]", default="nmap-bootstrap.xsl")
    parser.add_option('-t', '--threads', action="store", dest="threads", help="threads [maximum/default= 3]", default=3)
    parser.add_option('-o', '--output', action="store", dest="output", help="directory for saving the results")
    parser.add_option('--only-enumerate', action="store_false", dest="scan", help="only enumerate open ports using naabu", default=True)
    parser.add_option('--only-scan', action="store_false", dest="enumerate", help="only scan using nmap", default=True)
    parser.add_option('--nmap-param', action="store", dest="nmpara", help="nmap parameters [default= -Pn -A -T5]", default="-Pn -A -T5")
    parser.add_option('--naabu-param', action="store", dest="napara", help="naabu parameters [default= -top-ports 1000 -rate 800 -timeout 1500 -stats -retries 5]", default="-top-ports 1000 -rate 800 -timeout 1500 -stats -retries 5  ")

inputs, args = parser.parse_args()
if not inputs.list:
        parser.error(RED + "[!] input not given" + CLEAR)
if not inputs.output:
        parser.error(RED + "[!] output directory not provided" + CLEAR)
list = str(inputs.list)
verbose = inputs.verbose
output = str(inputs.output)
threads = int(inputs.threads)
enum = inputs.enumerate
scan = inputs.scan
template = str(inputs.template)
napara = inputs.napara
nmpara = inputs.nmpara

if(os.path.exists(output)==False):
    os.system("mkdir {0}".format(output))

if(os.path.exists(list)==False or os.stat(list).st_size == 0):
    parser.error(RED + "[!] input doesn't exists" + CLEAR)

if threads>3:
    threads=3



def nmapScan(target):
    host = target.split(" ")[0]
    ports = target.split(" ")[1]
    if verbose:
        print(GREEN + "[VERBOSE] started scanning {0}".format(host) + CLEAR)
    os.system("sudo nmap {3} -p {0} {1} -oX {2}/scan/{1}.xml > /dev/null".format(ports, host, output, nmpara))
    print(BLUE + "[+] completed scanning {0}".format(host) + CLEAR)

def mergeXML(xml, final):
    with open(final, mode = 'a', encoding='utf-8') as mergFile:
        with open(xml) as f:
            nMapXML = ET.parse(f)
            for host in nMapXML.findall('host'):
                cHost = ET.tostring(host, encoding='unicode', method='xml') 
                mergFile.write(cHost)
                mergFile.flush()

def generateHTML():
    files = set()
    for xmls in os.listdir(output+"/scan/"):
        if xmls.endswith('.xml'):
            files.add(os.path.join(output+"/scan/",xmls))
    final = output+"/scan.xml"
    out  = '<?xml version="1.0" encoding="UTF-8"?>'
    out += '<!DOCTYPE nmaprun>'
    out += '<nmaprun scanner="https://github.com/ARPSyndicate/NXScan">'
    file = open(final, "w")  
    file.write(out) 
    file.close()
    for xml in files:
        if xml.endswith('.xml'):
            mergeXML(xml, final)
    out = '<runstats><finished/></runstats></nmaprun>'
    file = open(final, "a")  
    file.write(out) 
    file.close()
    os.system("xsltproc -o {0} {1} {2}".format(output+"/scan.html", template, final))
    return

if enum:
    print(YELLOW + "[*] enumerating using naabu"+ CLEAR)
    os.system("sudo naabu -iL {0} -o {2}/enum.txt {1}".format(list, napara, output))
    list = "{0}/enum.txt".format(output)

if scan:
    print(YELLOW + "[*] scanning using nmap"+ CLEAR)
    os.system("mkdir {0}/scan".format(output))
    with open(list) as f:
        domains=f.read().splitlines()
    maps = defaultdict(set)
    for i in domains:
        maps[i.split(':')[0]].add(i.split(':')[1])
    targets = []
    for i in maps.keys():
        targets.append(i+" "+ ','.join(maps[i]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        try:
            executor.map(nmapScan, targets)
        except(KeyboardInterrupt, SystemExit):
            print(RED + "[!] interrupted" + CLEAR)
            executor.shutdown(wait=False)
            sys.exit()
    generateHTML()

print(YELLOW + "[*] done"+ CLEAR)