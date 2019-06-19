#!/usr/bin/env python

import dns.tsigkeyring
import dns.resolver
import dns.update
import dns.query
import dns.zone
import os

from dns.rdatatype import *
from flask import Flask, jsonify, request

app = Flask(__name__)

DNS_SERVER    = os.environ['SERVER']
TSIG_USERNAME = os.environ['TSIG_USERNAME']
TSIG_PASSWORD = os.environ['TSIG_PASSWORD']
VALID_ZONES   = [i + '.' for i in os.environ['ZONES'].split(',')]
RECORD_TYPES  = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']

@app.route('/dns/zone/<string:zone_name>', methods=['GET'])
def get_zone(zone_name):
    """
    Query a DNS zone file and get every record and return it in JSON
    format
    """
    records = {}

    if not zone_name.endswith('.'):
        zone_name = zone_name + '.'

    if zone_name not in VALID_ZONES:
        return jsonify({'error': 'zone file not permitted'})

    try:
        zone = dns.zone.from_xfr(dns.query.xfr(DNS_SERVER, zone_name))
    except dns.exception.FormError:
        return jsonify({'fail': zone_name})

    for (name, ttl, rdata) in zone.iterate_rdatas():
        if rdata.rdtype != SOA:
            if records.get(str(name), False):
                records[str(name)] = records[str(name)] + [{'Answer': str(rdata), 'RecordType': rdata.rdtype, 'TTL': ttl}]
            else:
                records[str(name)] = [{'Answer': str(rdata), 'RecordType': rdata.rdtype, 'TTL': ttl}]

    return jsonify({zone_name: records})


@app.route('/dns/record/<string:domain>', methods=['GET'])
def get_record(domain):
    """
    Allow users to request the records for a particular record
    """
    record = {}

    valid = len(filter(domain.endswith, VALID_ZONES)) > 0

    """
    Only allow the valid zones to be queried, this should stop
    TLD outside of your nameserver from being queried
    """
    if not valid:
        return jsonify({'error': 'zone not permitted'})

    for record_type in RECORD_TYPES:
        try:
            answers = dns.resolver.query(domain, record_type)
        except dns.resolver.NoAnswer:
            continue

        record.update({record_type: map(str, answers.rrset)})

    return jsonify({domain: record})


@app.route('/dns/record/<string:domain>/<int:ttl>/<string:record_type>/<string:response>', methods=['PUT', 'POST', 'DELETE'])
def dns_mgmt(domain, ttl, record_type, response):
    """
    Allow users to update existing records
    """
    zone = '.'.join(dns.name.from_text(domain).labels[1:])

    if record_type not in RECORD_TYPES:
        return jsonify({'error': 'not a valid record type'})

    if zone not in VALID_ZONES:
        return jsonify({'error': 'not a valid zone'})

    """
    If the user is only updating make sure the record exists before
    attempting to perform a dynamic update. This will
    """
    if request.method == 'PUT' or request.method == 'DELETE':
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [DNS_SERVER]
        
        try:
            answer = dns.resolver.query(domain, record_type)
        except dns.resolver.NXDOMAIN:
            return jsonify({'error': 'domain does not exist'})

    tsig = dns.tsigkeyring.from_text({TSIG_USERNAME: TSIG_PASSWORD})
    action = dns.update.Update(zone, keyring=tsig)

    if request.method == 'DELETE':
        action.delete(dns.name.from_text(domain).labels[0])
    elif request.method == 'PUT':
        action.replace(dns.name.from_text(domain).labels[0], ttl, str(record_type), str(response))

    elif request.method == 'POST':
        action.add(dns.name.from_text(domain).labels[0], ttl, str(record_type), str(response))
    try:
        response = dns.query.tcp(action, DNS_SERVER)
    except:
        return jsonify({'error': 'DNS transaction failed'})

    if response.rcode() == 0:
        return jsonify({domain: 'DNS request successful'})
    else:
        return jsonify({domain: 'DNS request failed'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
