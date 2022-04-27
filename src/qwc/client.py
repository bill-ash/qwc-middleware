"""
Simple client for sending raw qbxml to redis to be processed by the 
WebConnector on the next run.
"""

import walrus
import uuid
from qwc import config

class QBWCClient:
    """
    Python client for sending xml to a redis list where it will sit until queried by the 
    QuickBooks web connector. 
    """

    def  __init__(self):       
        self.redisdb = walrus.Database(
            host=config['redis']['host'],
            port=config['redis']['port'], 
            password=config['redis']['password'],
            db=config['redis']['db']
        )

    def sendxml(self, reqXML):
        """
        Connect to redis, create a unique id (ticket), and dump some xml to be 
        processed by QWC.
        Args:
            reqXML (xml): QBXML specification
        """
        # Create something to be processed ie: waitingWork
        waitingWork = self.redisdb.List('qwc:waitingWork')

        # Ticket to be processed 
        jobID =  "qwc:" + str(uuid.uuid1())
        
        # Create the response key to query info returned by QuickBooks to redis
        self.responsekey = 'qwc:response:' + jobID
        
        self.responselist = self.redisdb.List(self.responsekey)
        
        # Append work to be processed to redis list 
        waitingWork.append(jobID)

        wwh = self.redisdb.Hash(jobID)
        
        # Store the QBXML in redis 
        wwh['reqXML'] = reqXML

    def processResponse(self, processdata, optparam=""):
        """
        Subscribe to the redis response ticket waiting for QBWC to return data. 

        Process data is a function for printing info to the console
        """
        
        pubsub = self.redisdb.pubsub()
        
        pubsub.subscribe([self.responsekey])
        
        for item in pubsub.listen():
            # when the ticket returns end, unsubscribe from the channel
            if item['data'] == "end":
                pubsub.unsubscribe()
                self.responselist.clear()
                print("unsubscribed and finished")
                break
            elif item['data'] == "data":
                data = self.responselist.pop()
                
                if optparam:
                    processdata(data, optparam)
                else:
                    processdata(data)
    


