# qwc-middleware 

SOAP service for connecting to QuickBooks webconnector. 

Built using the framework built by Bill Barry in: https://github.com/BillBarry/pyqwc

Updated for use with python3, WebConnector version 2.3.0.207, and rapid proto-typing of 
different QuickBooks objects. 


# Useage 

qwc is a soap server with built in client that uses redis to queue raw QBXML to be processed
by the QuickBooks WebConnector. This is an asynchronous process that requires the client to listen
for when work has been completed by the QBWC. 

[client] >> sends qbxml >> [redis]

[QBWC] >> checks redis for new tickets >> [redis]

[redis] >> sends qbxml via ticket >> [QBWC]

[QBWC] >> process ticket and returns reslt/error >> [redis]

[client] >> query or subscribe to redis for result >> [redis]

Install the package in a fresh environment: 

```
python -m venv .venv 
```

then in install the package with pip:

```
python -m pip install qwc
```

Or get the latest development version from github: 

```
python -m pip install git+https::/github.com/bill-ash/qwc-middleware
```

If no `config.ini` file is found in the local directory, the default included with the package will be 
used: 

```
[qwc]
qbwfilename = ''

username = 'qbwcuser'
# Password entered when install the .qwc file to QuickBooks WebConnector.
password = 'test'
host = 'localhost'
port = 4244

[redis]
host = '127.0.0.1'
port = 6379
password = ''
db = 0
```

Install the `pyqwc.qwc` file to the QuickBooks WebConnector by opening the WebConnector, 
`File >> AppManagement >> Update Web Services` and choose `pyqwc.qwc`. The default password is `test`.


Start the service with: 

```
python -m qwc.scripts.start_server
```

Then, in a new terminal start a new session adding commands to be executed with the client. 


```
qwcClient = QBWCClient()

reqXML = add_customer('SuperCustomer123')

# Send the request to Redis to be processed by QuickBooks WebConnector 
qwcClient.sendxml(reqXML)
```

Check the examples directory for additional information. 

Once new work has been delivered to the Redis queue, run an update from the QuickBooks WebConnector 
to execute the pending work to be performed. 

## Sample .qwc file

Below is a sample .qwc file to be installed to the QuickBooks WebConnector: 

```
<?xml version="1.0"?>
<QBWCXML>
    <AppName>QWCTestService</AppName>
    <AppID></AppID>
    <AppURL>http://localhost:4244/qwc/</AppURL>
    <AppDescription>Python access to Quickbooks</AppDescription>
    <AppSupport>http://localhost:4244/</AppSupport>
    <UserName>qbwcuser</UserName>
    <OwnerID>{6801a7d2-3fb4-4643-8ef0-5e702b99521e}</OwnerID>
    <FileID>}495b6884-e33f-4dba-9ecc-a3bbad96a971}</FileID>
    <QBType>QBFS</QBType>
    <Scheduler>
        <RunEveryNMinutes>60</RunEveryNMinutes>
    </Scheduler>
</QBWCXML>
```

Save this file with a `.qwc` extension to successfully install to the WebConnector. 

## Example 

```
from qwc.client import QBWCClient
from qwc.objects import add_customer
from qwc.service import start_server

# Create the QBXML
customer = add_customer(name='BillAsh123')

# Start a new client 
client = QBWCClient()

# Deliver the QBXML to redis to be processed 
client.sendxml(customer)

# Start the server and then update the installed service from QuickBooks WebConnector
start_server()
```