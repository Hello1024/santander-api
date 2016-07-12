# Santander bank api
Santander UK bank API to log into internet banking and get a transaction list for your current or savings account.

## Example usage
```python
import Santander

# Connect and login
account = Santander.Santander('2511128396', {'What was your first school', 'London School'}, 'SecretPassword', '12345')

# List recent transactions
for tx in account.getTransactions():
  print tx

# Pay money out of my account
account.makePayment('10.00', '220877', '36829544', 'My Ref')
```

## Todo

* Multiple accounts
* Robust to malicious reference fields and names
* Better parsing of card transactions
* Support other banks
