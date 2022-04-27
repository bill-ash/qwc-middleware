"""
SOAP service served using wsgi and waitress. 
Implements six methods required for the QuickBooks WebConnector
to run in this order: 
- clientVersion() (accessed first but not required)
- authenticate() 
    - returns a ticket when new work is available to be processed from Redis
- sendRequestXML() 
    - sends qbxml to be processed (CRUD operation)
- receiveRequestXML()
    - processes the response if any
- getLastError()
    - dumps error message and code if any 
- closeConnection()
    - closed the connection when completed 

Query Manager 
Checks, processes, and iterates over any new work to be completed in Redis. 
"""
import uuid
import logging 
import walrus

from spyne.application import Application
from spyne.service import ServiceBase
from spyne.model.primitive import Integer, Unicode
from spyne.model.complex import Array
from spyne.decorator import srpc
from spyne.protocol.soap import Soap11
from lxml import etree
from spyne.server.wsgi import WsgiApplication
from waitress import serve

from qwc import config

DEBUG2 = 8
LEVELS = {'DEBUG2': DEBUG2,
          'DEBUG':logging.DEBUG,
          'INFO':logging.INFO,
          'WARNING':logging.WARNING,
          'ERROR':logging.ERROR,
          'CRITICAL':logging.CRITICAL,
          }

logging.addLevelName(DEBUG2, "DEBUG2")

logging.basicConfig(level=LEVELS['DEBUG'])

class QBWCService(ServiceBase):
    
    @srpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(strUserName, strPassword):
        """Authenticate the web connector to access this service.
        @param strUserName user name to use for authentication
        @param strPassword password to use for authentication
        @return the completed array
        """
        returnArray = []
        if strUserName == config['qwc']['username'] and strPassword == config['qwc']['password']:
            
            # checks first if there is a current active session 
            if session_manager.inSession():
                returnArray.append("none")
                # Busy, current active session 
                returnArray.append("busy")
                logging.debug('trying to authenticate during an open session')

            # If the session is not busy, check for new jobs 
            elif session_manager.newJobs():
                # set the ticket to the next avaiable ticket in the queue 
                sessionticket = session_manager.setTicket()
                
                # Return the ticket and the file name to indicate theer is new work to be done 
                returnArray.append(sessionticket)
                # returning the filename indicates there is a request in the queue
                returnArray.append(config['qwc']['qbwfilename']) 

            else:
                # don't return a ticket if there are no requests
                returnArray.append("none") 
                 #returning "none" indicates there are no requests at the moment
                returnArray.append("none")
        else:
            # don't return a ticket if username password does not authenticate
            returnArray.append("none") 
            returnArray.append('nvu')
        logging.debug('authenticate %s',returnArray)

        return returnArray

    @srpc(Unicode,  _returns=Unicode)
    def clientVersion(strVersion):
        """ sends Web connector version to this service
        @param strVersion version of GB web connector
        @return what to do in case of Web connector updates itself
        """
        logging.debug('clientVersion %s',strVersion)
        return ""

    @srpc(Unicode,  _returns=Unicode)
    def closeConnection(ticket):
        """ used by web connector to indicate it is finished with update session
        @param ticket session token sent from this service to web connector
        @return string displayed to user indicating status of web service
        """
        session_manager.closeSession()
        logging.debug('closeConnection %s',ticket)
        return "OK, all done!"

    @srpc(Unicode,Unicode,Unicode,  _returns=Unicode)
    def connectionError(ticket, hresult, message):
        """ used by web connector to report errors connecting to Quickbooks
        @param ticket session token sent from this service to web connector
        @param hresult The HRESULT (in HEX) from the exception 
        @param message error message
        @return string done indicating web service is finished.
        """
        # need to push this error to the client. Should there be a message channel on Redis for this?
        logging.debug('connectionError %s %s %s', ticket, hresult, message)
        return "done"

    @srpc(Unicode,  _returns=Unicode)
    def getLastError(ticket):
        """  Web connector error message
        @param ticket session token sent from this service to web connector
        @return string displayed to user indicating status of web service
        """
        logging.debug('lasterror {}'.forrmat(ticket))
        #return "Error message here!"
        return "NoOp"



    @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer,  _returns=Unicode)
    def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
        # ? maybe we could hang here, wait for some xml and send it to qwc, that way shortening the wait
        """ send request via web connector to Quickbooks
        @param ticket session token sent from this service to web connector
        @param strHCPResponse qbXML response from QuickBooks
        @param strCompanyFileName The Quickbooks file to get the data from
        @param qbXMLCountry the country version of QuickBooks
        @param qbXMLMajorVers Major version number of the request processor qbXML 
        @param qbXMLMinorVers Minor version number of the request processor qbXML 
        @return string containing the request if there is one or a NoOp
        """
        reqXML = session_manager.get_reqXML(ticket)
        logging.debug('sendRequestXML')
        logging.log(DEBUG2,'sendRequestXML reqXML %s ',reqXML)
        logging.log(DEBUG2,'sendRequestXML strHCPResponse %s ',strHCPResponse)
        return reqXML

    @srpc(Unicode,Unicode,Unicode,Unicode,  _returns=Integer)
    def receiveResponseXML(ticket, response, hresult, message):
        """ contains data requested from Quickbooks
        @param ticket session token sent from this service to web connector
        @param response qbXML response from QuickBooks
        @param hresult The HRESULT (in HEX) from any exception 
        @param message error message
        @return string integer returned 100 means done anything less means there is more to come.
              where can we best get that information?
        """
        logging.debug('receiveResponseXML %s %s %s',ticket,hresult,message)
        logging.log(DEBUG2,'receiveResponseXML %s',response)
        percent_done = session_manager.process_response(ticket, response)

        return percent_done




class SessionManager():
    
    def __init__(self):
        """
        Requests are read from redis and responses are returned in redis
        """
        self.redisdb= walrus.Database(
            host=config['redis']['host'],
            port=config['redis']['port'], 
            password=config['redis']['password'],
            db=config['redis']['db']
        )

        self.currentWork = self.redisdb.Hash('qwc:currentWork')
        self.waitingWork = self.redisdb.List('qwc:waitingWork')
        self.sessionKey = 'qwc:sessionTicket'

    def setTicket(self):
        sessionTicket = str(uuid.uuid1())
        self.redisdb.set(self.sessionKey, sessionTicket)
        
        return sessionTicket
    
    def clearTicket(self):
        sessionTicket = ""
        self.redisdb.set(self.sessionKey, sessionTicket)
        
        return sessionTicket
    
    def getTicket(self):
        
        return self.redisdb.get(self.sessionKey)
                         
    def inSession(self):
        return self.getTicket()

    def closeSession(self):
        self.clearTicket()
    
    def is_iterative(self,reqXML):
        root = etree.fromstring(str(reqXML))
        isIterator = root.xpath('boolean(//@iterator)')
        return isIterator

    def process_response(self, ticket, response):
        """
        Look for error responses here if you get an error, clear the redis keys and abort
        you don't know what is happening so better to bail out than try and fix things
        """
        # first store it
        reqID = self.currentWork['reqID'].decode('utf-8')
        responsekey = 'qwc:response:' + reqID
        self.responseStore = self.redisdb.List(responsekey)
        self.responseStore.append(response)
        self.redisdb.publish(responsekey, "data")
        
        logging.debug("storing response %s", responsekey)
        
        # check if it is iterative
        root = etree.fromstring(str(response))
        isIterator = root.xpath('boolean(//@iteratorID)')
        
        if isIterator:
            reqXML = self.currentWork['reqXML']
            reqroot = etree.fromstring(reqXML)
            iteratorRemainingCount = int(root.xpath('string(//@iteratorRemainingCount)'))
            iteratorID = root.xpath('string(//@iteratorID)')
            logging.info("iteratorRemainingCount %s",iteratorRemainingCount)
            
            if iteratorRemainingCount:
                # update the iterativeWork hash reqXML
                iteratornode =  reqroot.xpath('//*[@iterator]')
                iteratornode[0].set('iterator', 'Continue')
                requestID = int(reqroot.xpath('//@requestID')[0])
                iteratornode[0].set('requestID', str(requestID+1))
                iteratornode[0].set('iteratorID', iteratorID)
                ntree = etree.ElementTree(reqroot)
                nextreqXML = etree.tostring(ntree, xml_declaration=True, encoding='UTF-8')                
                self.currentWork['reqXML'] = nextreqXML
                
                # is there any reason to return an accurate number here? something less than 100 is all that is needed.
                return 50  
            
            else:
                # clear the currentWork hash
                self.currentWork.clear()
                
                # create a finish response
                self.redisdb.publish(responsekey, "end")
                
                #self.responseStore.append("TheEnd")
                
                if self.newJobs():
                    return 50
                else:
                    #100 percent done
                    return 100 
        else:
            self.redisdb.publish(responsekey, "end")
            #self.responseStore.append("TheEnd")        
            
            #100 percent done
            return 100

    def newJobs(self):
        if len(self.waitingWork):
            reqID = self.waitingWork.pop()
            wwh = self.redisdb.Hash(reqID)
            reqXML = wwh['reqXML']
            self.currentWork['reqXML'] = reqXML
            self.currentWork['reqID'] = reqID
            wwh.clear()
            
            return True
        
        else:
            return False
                                     
    def get_reqXML(self, ticket):
        return  self.currentWork['reqXML']
        
    def get_reqID(self, ticket):
        return  self.currentWork['reqID']


# Create the instance of a session manager to be used by the service 
# Handles commuinication with Redis 
session_manager = SessionManager()

# Wrap the service in an application layer - turning it into proper soap protocall 
app = Application([QBWCService],
    tns='http://developer.intuit.com/',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

# Wrap the soap application with a WSGI layer 
application  = WsgiApplication(app)


def start_server():
    """
    Serve the wsgi application using waitress server
    """
    # Use waitress as the server 
    serve(application, host=config['qwc']['host'], port=int(config['qwc']['port']))


