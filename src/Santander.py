import mechanize


class Santander:

  def __init__(self, customer_id, questions, password, security_number):
    self.br = br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Santander API (https://github.com/Hello1024/santander-api)')]
    
    page1 = br.open('https://retail.santander.co.uk/LOGSUK_NS_ENS/BtoChannelDriver.ssobto?dse_operationName=LOGON')
    br.select_form('formCustomerID_1')
    br['infoLDAP_E.customerID'] = customer_id
    response = br.submit()
    print response.read()
    
  def getTransactions():
    pass
