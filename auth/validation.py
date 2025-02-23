import csv

EMPLOYEE_CSV_PATH = 'employees.csv'  # Path to your CSV file in the root directory

def load_employee_list():
    employees = []
    with open(EMPLOYEE_CSV_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            employees.append(row['email'].strip().lower())
    return employees

def is_valid_employee(email):
    employees = load_employee_list()
    return email.lower() in employees
