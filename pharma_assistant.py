from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()
instructions = """You are a Pharmaceutical Knowledge Assistant.

Answer pharmaceutical questions using this structure:

1. Definition
2. Explanation
3. Pharmaceutical example
4. Key takeaway

Use clear language suitable for a B.Pharm student."""

while True:
    print("\n Pharmaceutical Knowledge Assistant ")
    print("1. Ask question: ")
    print("2. exit")

    choice = input("Enter choice: ")

    if choice == "1":
        question = input("PharmAI: ")
        if not question.strip():
            print("Please enter a question.")
        else:
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{instructions}\n\nUser question: {question.strip()}"
                    )
                print(response.text)
            except Exception as error:
                print(f"Something went wrong: {error}")
    elif choice == "2":
        print("PharmAI closing....")
        break
    else:
        print("Invalid choice. Please select 1 or 2.")