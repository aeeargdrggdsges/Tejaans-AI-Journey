# Function 1: Simple multiplication
def double(x):
    return x * 2

# Test it
print("double(5) =", double(5))
print("double(10) =", double(10))

# Function 2: Marks to Grade converter
def get_grade(marks):
    if marks >= 90:
        return "A+"
    elif marks >= 80:
        return "A"
    elif marks >= 70:
        return "B"
    elif marks >= 60:
        return "C"
    else:
        return "Need Improvement"

# Test with different marks
test_scores = [95, 85, 75, 65, 55]
for score in test_scores:
    print(f"Marks: {score} → Grade: {get_grade(score)}")

# Function 3: Calculate percentage
def calculate_percentage(obtained, total):
    return (obtained / total) * 100

print("\nPercentage:", calculate_percentage(450, 500), "%")