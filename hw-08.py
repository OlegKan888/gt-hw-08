from collections import UserDict
from datetime import datetime, timedelta
import pickle

# Базовий клас для полів запису
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для зберігання імені контакту. Ім'я не може бути порожнім
class Name(Field):
    def __init__(self, value):
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value)

# Клас для зберігання номера телефону. Має валідацію формату (10 цифр)
class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

# Клас для зберігання дня народження з перевіркою формату
class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime('%d.%m.%Y')

# Клас для зберігання інформації про контакт, включаючи ім'я, список телефонів та день народження
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    # Метод для додавання телефону
    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    # Метод для видалення телефону
    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    # Метод для редагування телефону
    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                return
        raise ValueError("Old phone number not found.")

    # Метод для пошуку телефону
    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    # Метод для додавання дня народження
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    # Метод для виведення інформації про запис у вигляді рядка
    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"

# Клас для зберігання та управління записами. Наслідується від UserDict
class AddressBook(UserDict):
    # Метод для додавання запису
    def add_record(self, record):
        self.data[record.name.value] = record

    # Метод для пошуку запису за ім'ям
    def find(self, name):
        return self.data.get(name, None)

    # Метод для видалення запису за ім'ям
    def delete(self, name):
        if name in self.data:
            del self.data[name]

    # Метод для виведення всіх записів у вигляді рядка
    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

    # Метод для отримання найближчих днів народжень
    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                if 0 <= (birthday_this_year - today).days <= 7:
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": birthday_this_year.strftime('%d.%m.%Y')
                    })
        return upcoming_birthdays

# Декоратор для обробки помилок
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return str(e)
    return inner

# Обробник для додавання дня народження
@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise ValueError("Usage: add-birthday [name] [birthday]")
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Added birthday {birthday} for {name}"
    return f"Contact {name} not found"

# Обробник для показу дня народження
@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise ValueError("Usage: show-birthday [name]")
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is {record.birthday}"
    return f"Contact {name} not found or no birthday set"

# Обробник для показу найближчих днів народжень
@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        return "\n".join([f"{item['name']}: {item['birthday']}" for item in upcoming])
    return "No upcoming birthdays"

# Основні команди бота
commands = {
    "add": lambda args, book: book.add_record(Record(args[0])), # Команда для додавання контакту
    "change": lambda args, book: book.find(args[0]).edit_phone(args[1], args[2]), # Команда для зміни телефону
    "phone": lambda args, book: str(book.find(args[0])), # Команда для показу телефону
    "all": lambda args, book: str(book), # Команда для показу всіх контактів
    "add-birthday": add_birthday, # Команда для додавання дня народження
    "show-birthday": show_birthday, # Команда для показу дня народження
    "birthdays": birthdays, # Команда для показу найближчих днів народжень
    "hello": lambda args, book: "Hello! How can I assist you?", # Привітання бота
    "close": lambda args, book: "Goodbye!", # Закриття програми
    "exit": lambda args, book: "Goodbye!" # Закриття програми
}

# Функція для розбору вхідного рядка
def parse_input(user_input):
    parts = user_input.split()
    command = parts[0]
    args = parts[1:]
    return command, args

# Основна функція для обробки команд
def handle_command(command, args, book):
    if command in commands:
        return commands[command](args, book)
    return "Unknown command"

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# Функція для десеріалізації
def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

# Основна функція для запуску бота
def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Goodbye!")
            save_data(book)
            break

        response = handle_command(command, args, book)
        print(response)

if __name__ == "__main__":
    main()