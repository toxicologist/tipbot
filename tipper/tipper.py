from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


class Connection:

    def __init__(self, user, passw, ip, port):
        self.con = AuthServiceProxy("http://%s:%s@%s:%d" % (user, passw, ip, port))

    def validate_address(self, address):
        validate = self.con.validate_address(address)
        return validate['isvalid']  # Returns True or False

    def get_address(self, account):
        return self.con.getaccountaddress(account)

    def get_balance(self, account, minconf=1):
        return self.con.get_balance(account, minconf)

    def withdraw(self, account, destination, amount):
        if amount > self.get_balance(account) or amount <= 0:
            raise ValueError("Invalid amount.")
        else:
            return self.con.sendfrom(account, destination, amount)

    def tip(self, account, destination, amount):
        if amount > self.get_balance(account) or amount <= 0:
            raise ValueError("Invalid amount.")
        else:
            self.con.move(account, destination, amount)

    def rain(self, account, amount):
        if amount > self.get_balance(account) or amount <= 0:
            raise ValueError("Invalid amount.")
        else:
            accounts = self.con.listaccounts()
            eachTip = amount / len(accounts)
            for ac in accounts:
                self.tip(account, ac, eachTip)
            return eachTip
