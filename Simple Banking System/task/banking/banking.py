# Write your code here
import string
import random
import sqlite3

MAIN_MENU_MESSAGE = """1. Create an account
2. Log into account
0. Exit
>"""

NEW_ACCOUNT_MESSAGE = """\nYour card has been created
Your card number:
{}
Your card PIN:
{}\n"""

LOGIN_ERROR_MESSAGE = """\nWrong card number or PIN!\n"""
LOGIN_SUCCESS_MESSAGE = """\nYou have successfully logged in!\n"""
LOGOUT_SUCCESS_MESSAGE = """\nYou have successfully logged out!\n"""

BALANCE_MENU_MESSAGE = """1. Balance
2. Add income
3. Do transfer
4. Close account
5. Log out
0. Exit
>"""
PROGRAM_EXIT_MESSAGE = "\nBye!\n"
INVALID_INPUT_MESSAGE = "\nInvalid input. Please try again.\n"


def lunh_func(x):
    idx, digit_str = x
    digit = int(digit_str)
    if idx % 2 == 1:
        digit *= 2
    if digit > 9:
        digit -= 9
    return digit


def get_checksum(card_number_exclude_last):
    checksum = sum(map(lunh_func, enumerate(card_number_exclude_last, start=1)))
    checksum = (10 - checksum % 10) % 10
    return str(checksum)


def is_pass_luhn_algorithm(card_number):
    expected_checksum = get_checksum(card_number[:-1])
    return expected_checksum == card_number[-1]


class Database:

    data_path = 'card.s3db'

    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS card (
                            id INTEGER PRIMARY KEY,
                            number TEXT,
                            pin TEXT,
                            balance INTEGER DEFAULT 0
                    );"""

    DELETE_TABLE = """DROP TABLE card;"""

    INSERT_NEW_CARD = """INSERT INTO card (number, pin) VALUES (?, ?);"""

    CHECK_VALID_CARD_PIN = """SELECT EXISTS (SELECT 1 FROM card 
                                             WHERE number=? AND pin=?
                                             LIMIT 1);"""

    CHECK_VALID_CARD = """SELECT EXISTS (SELECT 1 FROM card 
                                         WHERE number=?
                                         LIMIT 1);"""

    BALANCE_QUERY = """SELECT balance FROM card WHERE number=?;"""

    UPDATE_BALANCE = """UPDATE card
                        SET balance=?
                        WHERE number=?;
    """
    DELETE_ACCOUNT = """DELETE FROM card WHERE number=? AND pin=?"""

    @staticmethod
    def connect():
        return sqlite3.connect(Database.data_path)

    @staticmethod
    def create_table(connection):
        with connection:
            connection.execute(Database.CREATE_TABLE)

    @staticmethod
    def delete_table(connection):
        with connection:
            connection.execute(Database.DELETE_TABLE)

    @staticmethod
    def register_card(connection, card_no, pin):
        with connection:
            connection.execute(Database.INSERT_NEW_CARD, (card_no, pin))

    @staticmethod
    def is_valid_card_and_pin(connection, card_no, pin):
        with connection:
            match = connection.execute(Database.CHECK_VALID_CARD_PIN, (card_no, pin)).fetchone()[0]
        return match == 1

    @staticmethod
    def is_valid_card(connection, card_no):
        with connection:
            match = connection.execute(Database.CHECK_VALID_CARD, (card_no, )).fetchone()[0]
        return match == 1

    @staticmethod
    def get_balance(connection, card_no):
        with connection:
            result = connection.execute(Database.BALANCE_QUERY, (card_no, )).fetchone()[0]
        return result

    @staticmethod
    def set_balance(connection, card_no, balance):
        with connection:
            connection.execute(Database.UPDATE_BALANCE, (balance, card_no))

    @staticmethod
    def deposit(connection, card_no, amount):
        current_balance = Database.get_balance(connection, card_no)
        new_balance = current_balance + amount
        with connection:
            connection.execute(Database.UPDATE_BALANCE, (new_balance, card_no))

    @staticmethod
    def delete_account(connection, card_no, pin):
        with connection:
            connection.execute(Database.DELETE_ACCOUNT, (card_no, pin))

    @staticmethod
    def transfer_money(connection, card1, card2, amount):
        '''transfer money from card1 to card2 for the given amount'''
        balance1 = Database.get_balance(connection, card1)
        balance2 = Database.get_balance(connection, card2)
        if amount > balance1:
            return False
        new_balance1 = balance1 - amount
        new_balance2 = balance2 + amount
        Database.set_balance(connection, card1, new_balance1)
        Database.set_balance(connection, card2, new_balance2)
        return True


class BankAccount:

    IIN = '400000'
    ACCOUNT_LENGTH = 9
    PIN_LENGTH = 4

    def __init__(self, card_number=None, pin=None):
        if (card_number is None) and (pin is None):
            self.card_number, self.pin = self._generate_account()
        else:
            self.card_number = card_number
            self.pin = pin

    def _generate_account(self):
        card_number = self.IIN
        card_number += ''.join(random.choice(string.digits) for _ in range(self.ACCOUNT_LENGTH))
        card_number += get_checksum(card_number)   # dummy checksum
        pin = ''.join(random.choice(string.digits) for _ in range(self.PIN_LENGTH))
        return card_number, pin


def display_balance(conn, card_number):
    balance = Database.get_balance(conn, card_number)
    print("\nBalance: {}\n".format(balance))


def add_income(conn, card_number):
    income = input("\nEnter income:\n>")
    income = int(income)
    Database.deposit(conn, card_number, income)
    print("Income was added!\n")


def do_transfer(conn, card_number):
    target_card_no = input("""Transfer\nEnter card number:\n>""")
    if target_card_no == card_number:
        # same account transfer
        print("\nYou can't transfer money to the same account!\n")
    elif not is_pass_luhn_algorithm(target_card_no):
        print("\nProbably you made a mistake in the card number. Please try again!\n")
    elif not Database.is_valid_card(conn, target_card_no):
        print("\nSuch a card does not exist.\n")
    else:
        transfer_amount = input("\nEnter how much money you want to transfer:\n>")
        transfer_amount = int(transfer_amount)
        if Database.transfer_money(conn, card_number, target_card_no, transfer_amount):
            print("Success!\n")
        else:
            print("Not enough money!\n")


def close_account(conn, card_number, pin):
    Database.delete_account(conn, card_number, pin)
    print("\nThe account has been closed!\n")


def logout():
    print(LOGOUT_SUCCESS_MESSAGE)
    return False


def balance_exit():
    return True


def create_account(conn):
    new_account = BankAccount()
    Database.register_card(conn, new_account.card_number, new_account.pin)
    print(NEW_ACCOUNT_MESSAGE.format(new_account.card_number, new_account.pin))


def user_login(conn):
    user_card_number = input("\nEnter your card number:\n>")
    user_pin = input("Enter your PIN:\n>")
    if Database.is_valid_card_and_pin(conn, user_card_number, user_pin):
        user_account = BankAccount(user_card_number, user_pin)
        exit_program = balance_menu(conn, user_account)
        return exit_program
    else:
        print(LOGIN_ERROR_MESSAGE)
        return False   # continue main menu


def balance_menu(conn, account):
    print(LOGIN_SUCCESS_MESSAGE)
    while True:
        user_input = input(BALANCE_MENU_MESSAGE)
        if user_input == '1':
            display_balance(conn, account.card_number)
        elif user_input == '2':
            add_income(conn, account.card_number)
        elif user_input == '3':
            do_transfer(conn, account.card_number)
        elif user_input == '4':
            close_account(conn, account.card_number, account.pin)
        elif user_input == '5':
            return logout()
        elif user_input == '0':
            return balance_exit()
        else:
            print(INVALID_INPUT_MESSAGE)


def main_menu():

    # initialize accounts database
    conn = Database.connect()
    Database.create_table(conn)

    while True:
        user_input = input(MAIN_MENU_MESSAGE)
        if user_input == '0':
            print(PROGRAM_EXIT_MESSAGE)
            break
        elif user_input == '1':
            create_account(conn)
        elif user_input == '2':
            exit_program = user_login(conn)
            if exit_program:
                break
        else:
            print(INVALID_INPUT_MESSAGE)


if __name__ == '__main__':
    main_menu()