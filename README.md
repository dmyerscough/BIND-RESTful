BIND-RESTful
============

BIND RESTful API to perform dyanmic DNS updates and display the entire zone file.


Show Entire Zone
================

The simple GET reuqest will cause a zone transfer to occur and will provide JSON output for an entire zone file

`curl http://127.0.0.1:5000/dns/zone/internal.net`

Create DNS Entry
================

The simple POST request will create a domain called 'mynewhost.internal.net' with the IP address of 192.168.0.15

`curl -i -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/dns/record/mynewhost.internal.net/300/A/192.168.0.15`

Update DNS Entry
================

The simple PUT request updates the 'mynewhost.internal.net' to 192.168.0.13

`curl -i -H "Content-Type: application/json" -X PUT http://127.0.0.1:5000/dns/record/mynewhost.internal.net/300/A/192.168.0.13`
