"""
Default accounts, vendors, customers, etc. uses QB Enterprise Solutions 22.0
sample serivce based business `Larry's Landscaping & Garden Supply Co.`.
"""


def add_customer(name=None):
  if name is None:
    raise ValueError('Name is a required field')
  reqXML = """
    <?qbxml version="15.0"?>
      <QBXML>
        <QBXMLMsgsRq onError="stopOnError">
            <CustomerAddRq>
                <CustomerAdd><Name>{}</Name></CustomerAdd>
            </CustomerAddRq> 
        </QBXMLMsgsRq>
      </QBXML>
    """.format(name)
  return reqXML




def add_journal_entry(amount=10.23, memo="", date="2022-01-01"):
    reqXML = """
    <?qbxml version="15.0"?>
    <QBXML>
    <QBXMLMsgsRq onError = "stopOnError">
        <JournalEntryAddRq requestID = "1">
        <JournalEntryAdd>
            <TxnDate>{date}</TxnDate>
            <JournalDebitLine>
            <AccountRef>
                <FullName>Accounts Payable</FullName>
            </AccountRef>
            <Amount>{amount}</Amount>
            <Memo>{memo}</Memo> 
            <EntityRef>
                <FullName>ODI</FullName>
            </EntityRef>
            </JournalDebitLine>
            <JournalCreditLine>                     
            <AccountRef>
                <FullName>Cash Expenditures</FullName> 
            </AccountRef>
            <Amount>{amount}</Amount>
            <Memo>{memo}</Memo> 
            </JournalCreditLine>
        </JournalEntryAdd>
        </JournalEntryAddRq>
    </QBXMLMsgsRq>
    </QBXML>
    """.format(date=date, amount=amount, memo=memo)
    return reqXML


def add_credit_card_payment(credit_card='CalOil',
    vendor='ODI',
    date='2022-01-01',
    ref_number='3123',
    memo='MEMO',
    amount=102.12):
        
    reqXML = """
    <?qbxml version="15.0"?>
    <QBXML>
    <QBXMLMsgsRq onError="stopOnError">
        <CreditCardChargeAddRq>
            <CreditCardChargeAdd> <!-- required -->
            <AccountRef> <!-- required -->                                        
                <FullName>{credit_card}</FullName> <!-- optional -->
            </AccountRef>

            <PayeeEntityRef> <!-- optional -->
                <FullName >{vendor}</FullName> <!-- optional -->
            </PayeeEntityRef>
            
            <TxnDate >{date}</TxnDate> <!-- optional -->
            <RefNumber >{ref_number}</RefNumber> <!-- optional -->
            <Memo >{memo}</Memo> <!-- optional -->
            
            <ExpenseLineAdd> <!-- optional, may repeat -->
                <AccountRef> <!-- optional -->
                    <FullName >Tools and Misc. Equipment</FullName> <!-- optional -->
                </AccountRef>
                <Amount >{amount}</Amount> <!-- optional -->
                <Memo >Tools and stuff</Memo> <!-- optional -->
            </ExpenseLineAdd>
                    
            </CreditCardChargeAdd>
    </CreditCardChargeAddRq>
    </QBXMLMsgsRq>
    </QBXML>
    """.format(credit_card=credit_card, 
        vendor=vendor, date=date, ref_number=ref_number, memo=memo, amount=amount)

    return reqXML


