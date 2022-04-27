import walrus

# Import the client and the objects to be tested against QuickBooks
from qwc.client import QBWCClient
from qwc import config
from qwc.objects import *

# Connect to Redis
con = walrus.Database(
    host=config['redis']['host'],
    port=config['redis']['port'], 
    password=config['redis']['password'],
    db=config['redis']['db']
    )


# Clear out any work that was not properly handled on exit 
con.Hash('qwc:currentWork').clear()
con.List('qwc:waitingWork').clear()
con.set('qwc:sessionTicket','')


# Only grabs the most recent work added to the list - need to update to iterate over repeated work 
# will continue to add the same work over and over again if the percent returned is less that 100 
# instead of moving to the next piece of work. 
qwcClient = QBWCClient()

# Creates a single new customer and adds to the customer list... 
reqXML = add_customer(name='BadBoy')

# send the request to Redis to be processed by QuickBooks WebConnector 
qwcClient.sendxml(reqXML)

# Check the work to be preformed 
len(con.List('qwc:waitingWork'))


# How the manager looks for new work:
# reqID = con.List('qwc:waitingWork').pop()
# wwh = con.Hash(reqID)
# reqXML = wwh['reqXML']

# Create a subscription for when QB WebConnector processes the work and returns a response
# Listen for when QBWC connects to redis and starts processing the ticket 
pubsub = con.pubsub()
pubsub.subscribe([qwcClient.responsekey])

# The list WebConnector will publish the result too
# qwcClient.responselist

# Listen for a response:
for item in pubsub.listen():
    if item is not None:
        print('processing some data')
        print(item['data'])
        resp = item.get('data')
        print(resp)
        data = con.List(qwcClient.responsekey)
        print(data)


