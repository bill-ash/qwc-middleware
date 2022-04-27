from pyqwc import qbxml
import walrus
from pyqwc import clientlib
from lxml import etree
from configobj import ConfigObj


config = ConfigObj('config.ini')

reqXML = """
<?qbxml version="15.0"?>
<QBXML>
    <QBXMLMsgsRq onError="stopOnError">
        <CustomerAddRq>
            <CustomerAdd><Name>12O32thers</Name></CustomerAdd>
        </CustomerAddRq> <!-- optional -->
    </QBXMLMsgsRq>
</QBXML>
"""

reqXML = """
<?qbxml version="15.0"?>
<QBXML>
  <!-- onError may be set to continueOnError or stopOnError-->
  <QBXMLMsgsRq onError = "stopOnError">
    <JournalEntryAddRq requestID = "1">
      <JournalEntryAdd>
        <TxnDate>2022-04-23</TxnDate>
        
        <JournalDebitLine>
         <AccountRef>
            <FullName>Accounts Payable</FullName>
          </AccountRef>
          
          <Amount>10.23</Amount>
          <Memo>Debit Line</Memo> 
          <EntityRef>
            <FullName>ODI</FullName>
          </EntityRef>
        </JournalDebitLine>

        <JournalCreditLine>                     
          <AccountRef>
            <FullName>Cash Expenditures</FullName> 
          </AccountRef>
          <Amount>10.23</Amount>
          <Memo>My Credit Line</Memo> 
        </JournalCreditLine>
      </JournalEntryAdd>
    </JournalEntryAddRq>
  </QBXMLMsgsRq>
</QBXML>
"""


reqXML = """
<?qbxml version="15.0"?>
<QBXML>
        <QBXMLMsgsRq onError="stopOnError">
                <CreditCardChargeAddRq>
                        <CreditCardChargeAdd> <!-- required -->
                                <AccountRef> <!-- required -->                                        
                                        <FullName>CalOil Card</FullName> <!-- optional -->
                                </AccountRef>

                                <PayeeEntityRef> <!-- optional -->
                                        <FullName >ODI</FullName> <!-- optional -->
                                </PayeeEntityRef>
                                
                                <TxnDate >2025-01-01</TxnDate> <!-- optional -->
                                
                                <RefNumber >seven</RefNumber> <!-- optional -->
                                
                                <Memo >MyMemo</Memo> <!-- optional -->
                                
                                <ExpenseLineAdd> <!-- optional, may repeat -->
                                        <AccountRef> <!-- optional -->
                                                <FullName >Tools and Misc. Equipment</FullName> <!-- optional -->
                                        </AccountRef>
                                        
                                        <Amount >109.00</Amount> <!-- optional -->
                                        
                                        <Memo >Tools and stuff</Memo> <!-- optional -->
                                        
                                </ExpenseLineAdd>
                             
                        </CreditCardChargeAdd>
                        
                </CreditCardChargeAddRq>

        </QBXMLMsgsRq>
</QBXML>
"""

# Only grabs the most recent work added to the list - need to update to iterate over repeated work 
# will continue to add the same work over and over again if the percent returned is less that 100 
# instead of moving to the next piece of work. 
qwcClient = clientlib.pyqwcClient()

qwcClient.sendxml(reqXML)


con = walrus.Database(
            host=config['redis']['host'],
            port=config['redis']['port'], 
            password=config['redis']['password'],
            db=config['redis']['db'])


len(con.List('qwc:waitingWork'))
# reqID = con.List('qwc:waitingWork').pop()
# wwh = con.Hash(reqID)
# reqXML = wwh['reqXML']

pubsub = con.pubsub()
pubsub.subscribe([qwcClient.responsekey])
# qwcClient.responselist
# con.List('qwc:response:qwc:d01612cc-c437-11ec-a6d2-00155d4d2933')

# not sure I can subscribe to the issued response 
for item in pubsub.listen():
    if item is not None:
        print('processing some data')
        print(item['data'])
        zz = item.get('data')
        print(zz)
        data = con.List(qwcClient.responsekey)
        print(data)
