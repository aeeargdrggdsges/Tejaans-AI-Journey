#functon 1
def celcius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32
# Test it
print("celcius_to_fahrenheit(0) =", celcius_to_fahrenheit(0))   
print("celcius_to_fahrenheit(100) =", celcius_to_fahrenheit(100))
#function 2
def is_even_or_odd(number):
    if number % 2 == 0:
        return "Even"
    else:
        return "Odd"        
# Test with different numbers
test_numbers = [4, 7, 10, 13, 16]
for num in test_numbers:
    print(f"Number: {num} → {is_even_or_odd(num)}")