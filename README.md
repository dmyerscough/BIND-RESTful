BIND-RESTful
============

BIND RESTful API

Show Entire Zone
================

```curl http://127.0.0.1:5000/dns/zone/internal.net

Create DNS Entry
================

```curl -i -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/dns/record/create/mynewhost.internal.net/300/A/192.168.0.15

Update DNS Entry
================

```curl -i -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/dns/record/update/mynewhost.internal.net/300/A/192.168.0.13
