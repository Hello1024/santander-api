import mechanize
import BeautifulSoup
import re

class Transaction:
  def __init__(self, cols):
    self.date = cols[0]
    self.description = cols[1]
    self.billpay = False
    self.fasterpay = False
    self.name = None
    self.reference = None
    
    m = re.match(r"BILL PAYMENT FROM (.*), REFERENCE (.*)", self.description)
    if m:
      self.name, self.reference = m.groups()
      self.billpay = True
    
    m = re.match(r"FASTER PAYMENTS RECEIPT REF\.(.*) FROM (.*)", self.description)
    if m:
      self.reference, self.name = m.groups()
      self.fasterpay = True
    
    money_amount = cols[2] or cols[3]
    assert money_amount[0] == u'\xa3'
    self.amount_str = money_amount[1:]
    self.amount = float(money_amount[1:])
    if cols[3]:
      self.amount = -self.amount

  def __eq__(self, other):
    if isinstance(other, Transaction):
      return ((self.description == other.description) and (self.amount == other.amount) and (self.date == other.date))
    else:
      return False

  def __hash__(self):
    return hash(self.description)

  def __repr__(self):
    return str(self.__dict__)

class Santander:

  def __init__(self, customer_id, questions, password, security_number):
    """Create an object pointing at a santander online account
    
    Args:
      customer_id:   string representing a customer ID.  Eg. '12828282'
      questions:     dict of security questions and answers  Eg. {'Favourite food': 'pizza', 'favourite pet': 'cat'}
      password:      string account password
      security_number:  5 digit account security number.
    """
    self.br = br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Santander API (https://github.com/Hello1024/santander-api)')]
    
    page1 = br.open('https://retail.santander.co.uk/LOGSUK_NS_ENS/BtoChannelDriver.ssobto?dse_operationName=LOGON')
    br.select_form('formCustomerID_1')
    br['infoLDAP_E.customerID'] = customer_id
    self.response = br.submit()
    
    responsestr = self.response.read()
    
    found=0
    br.select_form(nr=0)
    
    if br.form.attrs['id'] == 'formCustomerID':
      for q,a in questions.iteritems():
        if q in responsestr:
          br['cbQuestionChallenge.responseUser'] = a
          found=found+1
      assert found==1

      self.response = br.submit()
      found=0    
      br.select_form(nr=0)
    
    assert br.form.attrs['id'] == 'formAuthenticationAbbey'
    for i in range(len(password)):
      for c in br.form.controls:
        if hasattr(c, 'id') and c.id == "signPosition" + str(i+1):
          c.value = password[i]
          found=found+1

    for i in range(len(security_number)):
      for c in br.form.controls:
        if hasattr(c, 'id') and c.id == "passwordPosition" + str(i+1):
          c.value = security_number[i]
          found=found+1
    
    print(found)
    assert found==6
    self.response = br.submit()
      
  def getTransactions(self, sort_code, account_number):
    """Download a transaction list for an account."""
    resp = self.br.open('https://retail.santander.co.uk/EBAN_Accounts_ENS/BtoChannelDriver.ssobto?dse_operationName=ViewTransactions').read()
    soup = BeautifulSoup.BeautifulSoup(resp)
    tx_table = soup.findAll("table",  {"class": "cardlytics_history_table data"})[0]
    rows = tx_table.findAll('tr')
    for row in rows:
      cols = row.findAll('td')
      cols = [ele.text.strip() for ele in cols]
      
      if len(cols) == 0:
        continue
      
      tx = Transaction(cols) 
      yield tx
  
  def makePayment(self, from_sort_code, from_account_number, amount, to_name, to_sort_code, to_account_number, to_reference):
    """  Not yet fully implemented.
    
    To set up:
      Log in to santander in a browser
      My details and settings
      Change OTP service phone number
      Put a number from https://www.textmagic.com/free-tools/receive-free-sms-online in.
    """
    assert amount > 0
    amount_pounds = int(amount)
    amount_pence = int((amount - amount_pounds)*100)
    
    # Receive SMS verification text
    br2 = mechanize.Browser()
    page_contents = br2.open("https://www.textmagic.com/free-tools/receive-free-sms-online/ajax/447520631303?page=1&perPage=10&query=&cmd=table").read()
    for line in page_contents.splitlines():
      m = re.match(r"This OTP is to MAKE A NEW PAYMENT for (.*) to account ending (.*). Don't share this code with anyone. Call immediately if you didn't request this (.*)</td>", line)
      if m:
        amt, acc, code = m.groups() 
        if amt == u'\xa3' + str(amount_pounds) + "." + str(amount_pence):
          pass
    
    
