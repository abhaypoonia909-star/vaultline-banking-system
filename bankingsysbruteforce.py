"""Original command-line banking system.

Preserved beside the Flask API in backend/ and the React app in frontend/.
accounts.txt is plaintext legacy storage and must never be committed.
Admin credentials are read from the environment so they are not stored in source.
"""

import csv
import hmac
import os
from typing import List, Dict, Optional

FILENAME = "accounts.txt"
MAX_ACCOUNTS = 10

def save_accounts_to_file(accounts: List[Dict]):
    with open(FILENAME, 'w', newline='') as file:
        writer = csv.writer(file)
        for acc in accounts:
            writer.writerow([
                acc['accountNumber'],
                acc['name'],
                acc['balance'],
                acc['pin'],
                acc['password']
            ])

def load_accounts_from_file() -> List[Dict]:
    accounts = []
    if not os.path.exists(FILENAME):
        return accounts
    with open(FILENAME, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 5:
                accounts.append({
                    'accountNumber': int(row[0]),
                    'name': row[1],
                    'balance': float(row[2]),
                    'pin': int(row[3]),
                    'password': row[4]
                })
    return accounts[:MAX_ACCOUNTS]

def create_account(accounts: List[Dict]):
    if len(accounts) >= MAX_ACCOUNTS:
        print("Account limit reached.")
        return

    acc = {}
    acc['accountNumber'] = len(accounts) + 1
    acc['name'] = input("Enter name: ").strip()
    acc['balance'] = float(input("Enter initial balance: "))
    acc['pin'] = int(input("Set 4-digit PIN: "))
    acc['password'] = input("Set password: ").strip()

    accounts.append(acc)
    save_accounts_to_file(accounts)
    print("Account created successfully.")

def login_user(accounts: List[Dict]) -> Optional[int]:
    try:
        acc_no = int(input("Enter account number: "))
        password = input("Enter password: ").strip()

        if acc_no < 1 or acc_no > len(accounts):
            print("Invalid account.")
            return None

        if accounts[acc_no - 1]['password'] == password:
            print("Login successful.")
            return acc_no
        else:
            print("Incorrect password.")
            return None
    except ValueError:
        print("Invalid input.")
        return None

def validate_pin(accounts, acc_no):
    pin = int(input("Enter PIN: "))
    return pin == accounts[acc_no - 1]['pin']

def display_account_details(accounts, acc_no):
    if validate_pin(accounts, acc_no):
        acc = accounts[acc_no - 1]
        print(acc)

def deposit_money(accounts, acc_no):
    if validate_pin(accounts, acc_no):
        amount = float(input("Enter amount: "))
        accounts[acc_no - 1]['balance'] += amount
        save_accounts_to_file(accounts)

def withdraw_money(accounts, acc_no):
    if validate_pin(accounts, acc_no):
        amount = float(input("Enter amount: "))
        if amount <= accounts[acc_no - 1]['balance']:
            accounts[acc_no - 1]['balance'] -= amount
            save_accounts_to_file(accounts)

def change_password(accounts, acc_no):
    old = input("Enter current password: ")
    if accounts[acc_no - 1]['password'] == old:
        accounts[acc_no - 1]['password'] = input("Enter new password: ")
        save_accounts_to_file(accounts)

def admin_login():
    expected_user = os.environ.get("ADMIN_USERNAME", "")
    expected_password = os.environ.get("ADMIN_PASSWORD", "")
    username = input("Admin username: ")
    password = input("Admin password: ")
    if not expected_user or not expected_password:
        print("Admin login is not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD.")
        return False
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(
        password, expected_password
    )

def view_all_accounts(accounts):
    for acc in accounts:
        print(acc)

def remove_account(accounts):
    try:
        acc_no = int(input("Enter account number to delete: "))
        if 1 <= acc_no <= len(accounts):
            del accounts[acc_no - 1]
            for i in range(len(accounts)):
                accounts[i]['accountNumber'] = i + 1
            save_accounts_to_file(accounts)
            print("Account deleted successfully.")
    except ValueError:
        print("Invalid input.")

# ✅ BRUTE FORCE ATTACK SIMULATION (ACCOUNT SELECTION ADDED)
def brute_force_simulation(accounts):
    print("\n--- Brute Force Attack Simulation ---")

    if not accounts:
        print("No accounts available.")
        return

    try:
        acc_no = int(input("Enter account number to attack: "))
        if acc_no < 1 or acc_no > len(accounts):
            print("Invalid account number.")
            return
    except ValueError:
        print("Invalid input.")
        return

    password_list = ["1234", "admin", "password", "test", "bank123", "abcd"]
    attempts = 0

    for pwd in password_list:
        attempts += 1
        print(f"Attempt {attempts}: Trying '{pwd}'")
        if accounts[acc_no - 1]['password'] == pwd:
            print(f"✅ Password cracked in {attempts} attempts!")
            return
        else:
            print("❌ Incorrect password")

    print("Simulation ended. Password not found.")

def main():
    accounts = load_accounts_from_file()

    while True:
        print("\nMain Menu")
        print("1. Create Account")
        print("2. Login as User")
        print("3. Login as Admin")
        print("4. Exit")
        print("5. Simulate Brute Force Attack")

        choice = input("Enter choice: ")

        if choice == '1':
            create_account(accounts)

        elif choice == '2':
            acc_no = login_user(accounts)
            if acc_no:
                while True:
                    print("\nUser Menu")
                    print("1. View Account")
                    print("2. Deposit")
                    print("3. Withdraw")
                    print("4. Change Password")
                    print("5. Logout")
                    uc = input("Enter choice: ")

                    if uc == '1':
                        display_account_details(accounts, acc_no)
                    elif uc == '2':
                        deposit_money(accounts, acc_no)
                    elif uc == '3':
                        withdraw_money(accounts, acc_no)
                    elif uc == '4':
                        change_password(accounts, acc_no)
                    elif uc == '5':
                        break

        elif choice == '3':
            if admin_login():
                while True:
                    print("\nAdmin Menu")
                    print("1. View Accounts")
                    print("2. Delete Account")
                    print("3. Logout")
                    ac = input("Enter choice: ")

                    if ac == '1':
                        view_all_accounts(accounts)
                    elif ac == '2':
                        remove_account(accounts)
                    elif ac == '3':
                        break

        elif choice == '4':
            break

        elif choice == '5':
            brute_force_simulation(accounts)

        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()