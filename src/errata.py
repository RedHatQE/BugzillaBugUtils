#!/usr/bin/python

import os
import sys
import urllib2
import base64
import json
import optparse
import getpass

api_base_url = 'https://errata.devel.redhat.com'

def load_data(url):
    request = urllib2.Request("%s%s" % (api_base_url, url))
    base64string = base64.encodestring('%s:%s' % (opts.username, opts.password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    fd = urllib2.urlopen(request)
    data = fd.read()
    fd.close()
    return json.loads(data)

def parse_args():
    parser=optparse.OptionParser(usage="Do something")
    parser.add_option("-u", "--username",
        action="store", default=getpass.getuser(),
        help="Errata tool username (default: %default)")
    parser.add_option("-p", "--password",
        action="store", default="",
        help="Errata tool password (will prompt if not provided)")
    parser.add_option("--rhnqa",
        action="store_true", default=False,
        help="Include TPS RHNQA results (default: %default)")

    (opts, args) = parser.parse_args()

    while not opts.username:
        opts.username = getpass.getuser()

    while not opts.password:
        opts.password = getpass.getpass("Enter Errata password: ")

    return (opts, args)

if __name__ == '__main__':

    (opts, args) = parse_args()

    advisory_dict = dict()
    advisory_by_tps = dict(GOOD=[], BAD=[], NOT_STARTED=[], INFO=[], VERIFY=[], BUSY=[])

    for advisory in load_data("/errata/errata_for_release/cloudforms%201_0?format=json"):
        advisory_dict[advisory.get("id")] = advisory
        #print "%s - %s" % (advisory.get("advisory_name"), advisory.get("synopsis"))
        tps_results = load_data("/tps/jobs_for_errata/%s.json" % advisory.get("id"))
        status = dict(GOOD=0, BAD=0, NOT_STARTED=0, INFO=0, VERIFY=0, BUSY=0)
        for tps_result in tps_results:
            # Skip rhnqa results for now
            if tps_result.get("rhnqa") and opts.rhnqa:
                continue

            if tps_result.get("state") == "WAIVED":
                tps_result["state"] = "GOOD"

            if not advisory.get("id") in advisory_by_tps[tps_result.get("state")]:
                advisory_by_tps[tps_result.get("state")].append(advisory.get("id"))
            #print "  * [{state}] - {link_text} ({host})".format(**tps_result)
        #print "%s - %s" % (advisory.get("advisory_name"), " ".join({"%s=%s" % (k,v) for k,v in status.items()}))

    # Display summary
    for state,advisory_list in advisory_by_tps.items():
        print " == Advisories with %s tps results ==" % state
        for aid in advisory_list:
            print " * {advisory_name} [{status}] - {synopsis} ({qe_owner})".format(**advisory_dict[aid])
        print
