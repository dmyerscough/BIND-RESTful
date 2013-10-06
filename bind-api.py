#!/usr/bin/env python

import ConfigParser
import dns.tsigkeyring
import dns.resolver
import dns.update
import dns.query
import dns.zone

from dns.rdatatype import *

from flask import Flask, jsonify
from werkzeug.routing import BaseConverter

app = Flask(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


def parse_config(config):
    """
    Parse the user config and retreieve the nameserver, username and
    password required to perform dynamic DNS updates
    """
    options = {}
    parser = ConfigParser.ConfigParser()
    parser.read(config)

    options['nameserver'] = parser.get('Nameserver', 'nameserver')
    options['username'] = parser.get('Auth', 'username')
    options['password'] = parser.get('Auth', 'password')

    options['zones'] = [i + '.' for i in parser.get('Zones', 'valid').split(",")]

    return options


@app.route('/dns/zone/<string:zone_name>', methods=['GET'])
def get_zone(zone_name):
    """
    Query a DNS zone file and get every record and return it in JSON
    format
    """
    config = parse_config('config.ini')

    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']
    valid_zones = config['zones']

    records = {}

    if not zone_name.endswith('.'):
        zone_name = zone_name + '.'

    if zone_name not in valid_zones:
        return jsonify({'error': 'zone file not permitted'})

    try:
        zone = dns.zone.from_xfr(dns.query.xfr(config['nameserver'], zone_name))
    except dns.exception.FormError:
        return jsonify({'fail': zone_name})

    for (name, ttl, rdata) in zone.iterate_rdatas():
        if rdata.rdtype != SOA:
            if records.get(str(name), 0):
                records[str(name)] = records[str(name)] + [{'Answer': str(rdata), 'RecordType': rdata.rdtype, 'TTL': ttl}]
            else:
                records[str(name)] = [{'Answer': str(rdata), 'RecordType': rdata.rdtype, 'TTL': ttl}]

    return jsonify({zone_name: records})


@app.route('/dns/record/<string:domain>', methods=['GET'])
def get_record(domain):
    """
    Allow users to request the records for a particualr record
    """
    config = parse_config('config.ini')

    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']
    valid_zones = config['zones']

    record = {}

    valid = [True for i in valid_zones if domain.endswith(i)]

    """
    Only allow the valid zones to be queried, this should stop
    TLD outside of your nameserver from being queried
    """
    if valid:
        for record_type in record_types:
            try:
                answers = dns.resolver.query(domain, record_type)
            except dns.resolver.NoAnswer:
                continue

            record.update({record_type: [str(i) for i in answers.rrset]})

        return jsonify({domain: record})
    else:
        return jsonify({'error': 'zone not permitted'})


@app.route('/dns/record/<regex("update|create"):action>/<string:domain>/<int:ttl>/<string:record_type>/<string:response>', methods=['PUT', 'POST'])
def dns_mgmt(action, domain, ttl, record_type, response):
    """
    Allow users to update existing records
    """
    config = parse_config('config.ini')

    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']
    valid_zones = config['zones']

    zone = ''
    zone = '.'.join(dns.name.from_text(domain).labels[1:])

    if record_type not in record_types:
        return jsonify({'error': 'not a valid record type'})

    if zone not in valid_zones:
        return jsonify({'error': 'not a valid zone'})

    """
    If the user is only updating make sure the record exists before
    attempting to perform a dynamic update. This will
    """
    if action == 'update':
        try:
            answer = dns.resolver.query('.'.join([domain, zone]), record_type)
        except dns.resolver.NXDOMAIN:
            return jsonify({'error': 'does not exist'})

    tsig = dns.tsigkeyring.from_text({config['username']: config['password']})

    update = dns.update.Update(zone, keyring=tsig)
    update.replace(dns.name.from_text(domain).labels[0], ttl, str(record_type), str(response))

    try:
        response = dns.query.tcp(update, config['nameserver'])
    except:
        return jsonify({'error': 'unable to update domain'})

    if response.rcode() == 0:
        return jsonify({domain: 'successfully updated'})
    else:
        return jsonify({domain: 'failed to update'})


if __name__ == '__main__':
    app.run(debug=True)
