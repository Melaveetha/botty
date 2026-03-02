import os
from dotenv import load_dotenv
from botty import AppBuilder, SQLiteProvider

load_dotenv()


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Missing BOT_TOKEN")
        return

    app = AppBuilder().token(token).database(SQLiteProvider("media.db")).build()
    app.launch()


if __name__ == "__main__":
    main()
