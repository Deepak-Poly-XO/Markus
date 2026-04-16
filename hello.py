# Calculator Program

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Division by zero"
    return a / b

def calculator():
    print("=== Simple Calculator ===")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    print()

    while True:
        try:
            num1 = input("Enter first number: ")
            if num1.lower() == 'quit':
                print("Goodbye!")
                break

            operator = input("Enter operator (+, -, *, /): ")
            if operator.lower() == 'quit':
                print("Goodbye!")
                break

            num2 = input("Enter second number: ")
            if num2.lower() == 'quit':
                print("Goodbye!")
                break

            num1 = float(num1)
            num2 = float(num2)

            if operator == '+':
                result = add(num1, num2)
            elif operator == '-':
                result = subtract(num1, num2)
            elif operator == '*':
                result = multiply(num1, num2)
            elif operator == '/':
                result = divide(num1, num2)
            else:
                print("Invalid operator. Please use +, -, *, /")
                continue

            print(f"Result: {num1} {operator} {num2} = {result}")
            print()

        except ValueError:
            print("Invalid input. Please enter numeric values.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    calculator()
