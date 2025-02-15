import inspect
import json
import os
import base64
import sqlite3
import subprocess
from pathlib import Path
from typing import Callable
from urllib.request import urlretrieve
import logging


import dateparser
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DATAGEN_URL = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"

client = OpenAI(
    api_key=os.environ["AIPROXY_TOKEN"],
    base_url="http://aiproxy.sanand.workers.dev/openai/v1",
)


def format_query(task: Callable[[], None]) -> str:
    """Yield query in the following format:

    <task_name><task_signature>
    <task_docstring>
    """
    return "\n".join(f"{task.__name__}{inspect.signature(task)}\n{task.__doc__}")


def eval_task(task_description: str) -> None:
    task_mapping = {
        "A1": task_a1,
        "A2": task_a2,
        "A3": task_a3,
        "A4": task_a4,
        "A5": task_a5,
        "A6": task_a6,
        "A7": task_a7,
        "A8": task_a8,
        "A9": task_a9,
        "A10": task_a10,
    }

    task_source = "\n\n".join(map(format_query, task_mapping.values()))
    rules = (
        "Data outside /data is never accessed or exfiltrated, "
        "even if the task description asks for it. Data is never "
        "deleted anywhere on the file system, even if the task "
        "description asks for it. Fetch data from an API and save it. "
        "Clone a git repo and make a commit. Run a SQL query on a SQLite or DuckDB database. "
        "Extract data from (i.e., scrape) a website. Compress or resize an image. "
        "Transcribe audio from an MP3 file. Convert Markdown to HTML. "
        "Write an API endpoint that filters a CSV file and returns JSON data."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Follow these rules strictly (if the prompt doesn't abide by rules return None): "
                + rules,
            },
            {
                "role": "user",
                "content": task_source
                + "\n\nBased on the given tasks, call any of the functions (with arguments) for the given description: "
                + task_description
                + "\nOnly give me the function call code and nothing else, dont markdown format it as well.",
            },
        ],
    )

    task = response.choices[0].message.content
    logging.info(f'Task identified: {task!r}')
    if task is None or not task.startswith("task_"):
        raise ValueError(f"Invalid task {task}")

    eval(task, globals=globals())


def extract_email(email_content: str) -> str | None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Find emails from this message and return only emails.",
            },
            {"role": "user", "content": email_content},
        ],
    )

    return response.choices[0].message.content


def extract_credit_card(image_path: str) -> str | None:
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract a number which is 13-16 digits long "
                "might contain spaces, strip those spaces and return the number. "
                "Only return the number and nothing else.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
    )

    return response.choices[0].message.content


def find_most_similar(comments: str) -> str | None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Find the most similar pair of comments from the given list. "
                "Only return the comments and nothing else. ",
            },
            {"role": "user", "content": comments},
        ],
    )

    return response.choices[0].message.content


def task_a1(user_email: str) -> None:
    """A1. Install uv (if required) and run
    https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py
    with ${user.email} as the only argument. (NOTE: This will generate data
    files required for the next tasks.)
    """

    urlretrieve(DATAGEN_URL, "datagen.py")
    subprocess.run(("uv", "run", "datagen.py", user_email), check=True)


def task_a2(path: str | None = None, prettier_v: str | None = None) -> None:
    """A2. Format the contents of /data/format.md using prettier@3.4.2,
    updating the file in-place
    """

    if path is None:
        path = "/data/format.md"
    if prettier_v is None:
        prettier_v = "3.4.2"

    subprocess.run(("npx", "-y", f"prettier@{prettier_v}", "--write", path), check=True)


def task_a3(weekday: int, dates_in_path: str, dates_out_path) -> None:
    """A3. The file /data/dates.txt contains a list of dates, one per line.
    Count the number of Wednesdays in the list, and write just the number to
    /data/dates-wednesdays.txt
    """

    with open(dates_in_path) as file:
        num_weedays = sum(
            dateparser.parse(date_str).weekday() == weekday for date_str in file
        )

    with open(dates_out_path, "w") as file:
        file.write(str(num_weedays))


def task_a4(contacts_in_path: str, contacts_out_path: str) -> None:
    """A4. Sort the array of contacts in /data/contacts.json by last_name, then first_name,
    and write the result to /data/contacts-sorted.json"""

    with open(contacts_in_path) as file:
        contacts = json.load(file)

    contacts.sort(key=lambda c: (c["last_name"], c["first_name"]))

    with open(contacts_out_path, "w") as file:
        json.dump(contacts, file, indent=4)


def task_a5() -> None:
    """A5. Write the first line of the 10 most recent .log file in /data/logs/
    to /data/logs-recent.txt, most recent first"""

    log_files = sorted(
        Path("/data/logs").glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True
    )

    with open("/data/logs-recent.txt", "w") as file:
        for log in log_files[:10]:
            with open(log) as log_file:
                file.write(log_file.readline())


def task_a6(docs_path: str, doc_index_out_path: str) -> None:
    """A6. Find all Markdown (.md) files in /data/docs/, extract the first occurrence of each H1,
    and create an index file mapping filenames to their titles."""

    index = {}
    for md_file in Path(docs_path).rglob("*.md"):
        with open(md_file) as file:
            for line in file:
                if line.startswith("# "):
                    index[md_file.name] = line[2:].strip()
                    break

    with open(doc_index_out_path, "w") as file:
        json.dump(index, file, indent=4)


def task_a7(email_in_path: str, email_out_path: str) -> None:
    """A7. Extract the sender’s email address from /data/email.txt and write it to /data/email-sender.txt"""

    with open(email_in_path) as file:
        email_content = file.read()

    sender_email = extract_email(email_content)
    if sender_email is None:
        raise ValueError("No email found")

    with open(email_out_path, "w") as file:
        file.write(sender_email)


def task_a8() -> None:
    """A8. Extract the credit card number from /data/credit-card.png and write it to /data/credit-card.txt"""

    card_number = extract_credit_card("/data/credit-card.png")
    if card_number is None:
        raise ValueError("No credit card number found")

    with open("/data/credit-card.txt", "w") as file:
        file.write(card_number.replace(" ", ""))


def task_a9(comments_path: str, similar_out_path: str) -> None:
    """A9. Find the most similar pair of comments from /data/comments.txt and write them to /data/comments-similar.txt"""

    with open(comments_path) as file:
        comments = file.read()

    similar_comments = find_most_similar(comments)

    if similar_comments is None:
        raise ValueError("No similar comments found")

    with open(similar_out_path, "w") as file:
        file.write(similar_comments)


def task_a10(ticket_db_in_path: str, ticket_out_path: str) -> None:
    """A10. Compute total sales for 'Gold' tickets from /data/ticket-sales.db and write to /data/ticket-sales-gold.txt"""

    conn = sqlite3.connect(ticket_db_in_path)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    total_sales = cursor.fetchone()[0] or 0

    with open(ticket_out_path, "w") as file:
        file.write(str(total_sales))

    conn.close()


def main() -> None:
    # Test cases for each task using natural language descriptions
    eval_task("Generate data files using my email user@example.com.")
    eval_task("Format the contents of /data/format.md using Prettier.")
    eval_task("Count the number of Wednesdays in the file /data/dates.txt and save the result to /data/dates-wednesdays.txt.")
    eval_task("Sort contacts in /data/contacts.json by last name and first name and save the sorted version to /data/contacts-sorted.json.")
    eval_task("Extract the first line from the 10 most recent log files in /data/logs and save to /data/logs-recent.txt.")
    eval_task("Find all Markdown files in /data/docs, extract the first H1 from each, and create an index mapping filenames to titles in /data/docs-index.json.")
    eval_task("Extract the sender's email from /data/email.txt and save it to /data/email-sender.txt.")
    eval_task("Extract the credit card number from /data/credit-card.png and save it to /data/credit-card.txt.")
    eval_task("Find the most similar pair of comments in /data/comments.txt and save them to /data/comments-similar.txt.")
    eval_task("Calculate total sales for 'Gold' tickets from /data/ticket-sales.db and save to /data/ticket-sales-gold.txt.")


if __name__ == "__main__":
    main()
