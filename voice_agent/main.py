# main.py

from app.core.pipeline import run_pipeline


def run_conversation():
    user_input = input("You: ")

    response = run_pipeline(user_input)

    print("System:", response["response"])


if __name__ == "__main__":
    while True:
        run_conversation()
