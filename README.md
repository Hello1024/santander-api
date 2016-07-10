# Santander bank api
Santander UK bank API to log into internet banking and get a transaction list for your current or savings account.

## Example usage
```python
import Santander

account = Santander.Santander('2511128396', {'What was your first school', 'London School'}, 'SecretPassword', '12345')

for tx in account.GetTransactions('123212', '93729511'):
  print tx
```

## Todo

* Sending money
* Multiple accounts
* Robust to malicious reference fields and names
* Handling of logon session timeouts
* Better parsing of card transactions
* Support other banks
