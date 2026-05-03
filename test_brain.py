from brain.mind import think

print("Brain test — type something and FRIDAY will respond.")
print("Type 'quit' to exit.\n")

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() == "quit":
        break
    
    if not user_input:
        continue

    response = think(user_input)
    print(f"FRIDAY: {response}\n")