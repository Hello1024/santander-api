import mechanize
import BeautifulSoup
import re
import time

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
    self.br = mechanize.Browser()
    self.br.addheaders = [('User-agent', 'Santander API (https://github.com/Hello1024/santander-api)')]
    self.customer_id = customer_id
    self.questions = questions
    self.password = password
    self.security_number = security_number
    self.cachedTransactionSoupTime = 0
    
  def _loginAndOpen(self, url):
    br = self.br
    page1 = br.open(url)
    
    # Not now on the login page?  We're probably logged in!
    if 'formCustomerID_1' not in [x.name for x in list(br.forms())]:
      return

    br.select_form('formCustomerID_1')
    br['infoLDAP_E.customerID'] = self.customer_id
    self.response = br.submit()
    
    responsestr = self.response.read()
    found=0
    br.select_form(nr=0)
    
    if br.form.attrs['id'] == 'formCustomerID':
      for q,a in self.questions.iteritems():
        if q in responsestr:
          br['cbQuestionChallenge.responseUser'] = a
          found=found+1
      assert found==1, "Looks like you have the wrong authentication questions"

      self.response = br.submit()
      found=0    
      br.select_form(nr=0)
    
    assert br.form.attrs['id'] == 'formAuthenticationAbbey', "Looks like you have the wrong customer ID or authentication answers"
    for i in range(len(self.password)):
      for c in br.form.controls:
        if hasattr(c, 'id') and c.id == "signPosition" + str(i+1):
          c.value = self.password[i]
          found=found+1

    for i in range(len(self.security_number)):
      for c in br.form.controls:
        if hasattr(c, 'id') and c.id == "passwordPosition" + str(i+1):
          c.value = self.security_number[i]
          found=found+1
    
    assert found==6
    self.response = br.submit()
    self.response = br.open(url)
    assert 'formCustomerID_1' not in [x.name for x in list(br.forms())], "Login probably failed"
    

  def selectAccount(self, sort_code, account_number):
    """Unimplemented"""
    pass


  def _uncachedGetViewTransactionsSoup(self):
    self._loginAndOpen('https://retail.santander.co.uk/EBAN_Accounts_ENS/BtoChannelDriver.ssobto?dse_operationName=ViewTransactions')
    return BeautifulSoup.BeautifulSoup(self.response.read())

  # We cache this by default because santanders data isn't always up to date
  # and you'll get banned if a runaway script polls this every few seconds.
  def _getViewTransactionsSoup(self):
    if self.cachedTransactionSoupTime + 60 < time.time():
      self.cachedTransactionSoupTime = time.time()
      self.cachedTransactionSoup = self._uncachedGetViewTransactionsSoup()
    return self.cachedTransactionSoup
  
  def getBalance(self):
    """Gets current and available balance.

    Returns:
       (current_balance, available_balance) tuple.
    """
    soup = self._getViewTransactionsSoup()
    bbox = soup.findAll("div",  {"class": "transationList"})[0]
    m = re.match(ur".*Current balance:\xa3(\d+\.\d\d)Available balance:\xa3(\d+\.\d\d).*", bbox.getText())
    assert m
    return m.groups()
    
      
  def getTransactions(self):
    """Download a transaction list for an account.
    
    Returns:
      A generator which yields Transaction objects for recent transactions.
    """
    soup = self._getViewTransactionsSoup()
    tx_table = soup.findAll("table",  {"class": "cardlytics_history_table data"})[0]
    rows = tx_table.findAll('tr')
    for row in rows:
      cols = row.findAll('td')
      cols = [ele.text.strip() for ele in cols]
      
      if len(cols) == 0:
        continue
      
      tx = Transaction(cols) 
      yield tx
  
  def makePayment(self, amount, to_name, to_sort_code, to_account_number, to_reference):
    """Makes a payment from your account to a remote account.
    
    To set up:
      Log in to santander in a browser
      My details and settings
      Change OTP service phone number
      Put a number from https://www.textmagic.com/free-tools/receive-free-sms-online in.

    Sets up the payment, receives an SMS verification code, then returns when
    the right code is received.   Expect this call to take ~30 seconds to
    return.

    Args:
      All args are strings.
    """
    # Amount should be formed like "0.00", no thousands seperators.
    m = re.match(r"^(\d+)\.(\d{2})$", amount)
    assert m
    amount_pounds, amount_pence = m.groups()

    to_sort_code = re.sub("\D", "", to_sort_code)
    assert len(to_sort_code) == 6
    assert to_account_number.isdigit()
    assert len(to_account_number) == 8
    

    self._loginAndOpen('https://retail.santander.co.uk/EBAN_Payees_ENS/BtoChannelDriver.ssobto?dse_operationName=setUpNewPayment')

    self.br.follow_link(text_regex="Pay a new person")
    self.br.select_form('formDatas')
    self.br['formDatas.paymentName'] = to_name
    self.br['formDatas.inoutAccount.1'] = to_sort_code[0:2]
    self.br['formDatas.inoutAccount.2'] = to_sort_code[2:4]
    self.br['formDatas.inoutAccount.3'] = to_sort_code[4:6]
    self.br['formDatas.inoutAccount.0'] = to_account_number
    self.br['formDatas.inoutAccount.5'] = to_reference
    self.br['formDatas.amount.amount.integer'] = amount_pounds
    self.br['formDatas.amount.amount.fractional'] = amount_pence
    self.response = self.br.submit(name='formDatas.buttons.1', label="Continue >")


    while len([x for x in list(self.br.forms()) if x.name=="signOtpSetUpPay"]):
      self.br.select_form('signOtpSetUpPay')
      used_codes = set()
      verify_code = ''
      while verify_code == '':
        time.sleep(5)

        # Receive SMS verification text
        br2 = mechanize.Browser()
        page_contents = br2.open("https://www.textmagic.com/free-tools/receive-free-sms-online/ajax/447520631303?page=1&perPage=10&query=&cmd=table").read()
        for line in page_contents.splitlines():
          m = re.match(r".*This OTP is to MAKE A NEW PAYMENT for (.*) to account ending (.*). Don&#039;t share this code with anyone. Call immediately if you didn&#039;t request this (.*)</td>.*", line)
          if m:
            amt, acc, code = m.groups() 
            if amt == '\xc2\xa3' + amount_pounds + "." + amount_pence and acc == to_account_number[-4:]:
              if code not in used_codes:
                verify_code = code
                break
    
      used_codes.add(verify_code)

      self.br['signOtpSetUpPay.sign.fields.0'] = verify_code
      self.response = self.br.submit(name='signOtpSetUpPay.actions.2', label='Confirm')
 

