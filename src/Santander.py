import mechanize
import BeautifulSoup

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
    soup = BeautifulSoup(resp, 'html.parser')
    
    
