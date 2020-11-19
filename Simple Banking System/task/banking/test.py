import unittest
from .banking import BankAccount, Database


class AccountTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.conn = Database.connect()
        Database.create_table(self.conn)
        self.account_1 = BankAccount()
        Database.register_card(self.conn, self.account_1.card_number, self.account_1.pin)
        self.account_2 = BankAccount()
        Database.register_card(self.conn, self.account_2.card_number, self.account_2.pin)

    def tearDown(self) -> None:
        Database.delete_table(self.conn)

    def test_deposit(self):
        amount = 10000
        balance = Database.get_balance(self.conn, self.account_1.card_number)
        self.assertEqual(balance, 0)
        Database.deposit(self.conn, self.account_1.card_number, amount)
        balance = Database.get_balance(self.conn, self.account_1.card_number)
        self.assertEqual(balance, amount)

    def test_over_transfer(self):
        amount = 10000
        Database.deposit(self.conn, self.account_1.card_number, amount)
        balance1 = Database.get_balance(self.conn, self.account_1.card_number)
        self.assertEqual(balance1, amount)
        balance2 = Database.get_balance(self.conn, self.account_2.card_number)
        self.assertEqual(balance2, 0)
        transfer = 15000
        result = Database.transfer_money(self.conn, self.account_1.card_number,
                                         self.account_2.card_number, transfer)
        self.assertFalse(result)
        balance1_after = Database.get_balance(self.conn, self.account_1.card_number)
        balance2_after = Database.get_balance(self.conn, self.account_2.card_number)
        self.assertEqual(balance1, balance1_after)
        self.assertEqual(balance2, balance2_after)

    def test_ok_transfer(self):
        amount = 10000
        Database.deposit(self.conn, self.account_1.card_number, amount)
        balance1 = Database.get_balance(self.conn, self.account_1.card_number)
        self.assertEqual(balance1, amount)
        balance2 = Database.get_balance(self.conn, self.account_2.card_number)
        self.assertEqual(balance2, 0)
        transfer = 5000
        result = Database.transfer_money(self.conn, self.account_1.card_number,
                                         self.account_2.card_number, transfer)
        self.assertTrue(result)
        balance1_after = Database.get_balance(self.conn, self.account_1.card_number)
        balance2_after = Database.get_balance(self.conn, self.account_2.card_number)
        self.assertEqual(balance2 + transfer, balance2_after)
        self.assertEqual(balance1-transfer, balance1_after)


if __name__ == '__main__':
    unittest.main()
