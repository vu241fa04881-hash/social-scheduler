import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from scheduler.scheduler import add_job
from scheduler.database import (
    create_table,
    add_post,
    get_posts
)

from app.publisher import publish_post

create_table()


def schedule_post():

    topic = topic_entry.get("1.0", tk.END).strip()
    date = date_entry.get().strip()
    time = time_entry.get().strip()

    if not topic:
        messagebox.showerror(
            "Error",
            "Enter topic"
        )
        return

    try:

        run_time = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        )

        add_job(
            run_time,
            publish_post,
            topic
        )

        add_post(
            topic,
            run_time.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        messagebox.showinfo(
            "Success",
            "Post Scheduled Successfully"
        )

        topic_entry.delete("1.0", tk.END)
        load_posts()

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e)
        )


def load_posts():

    post_list.delete(
        0,
        tk.END
    )

    posts = get_posts()

    for post in posts:
        display_topic = post[1].replace("\n", " ")
        if len(display_topic) > 80:
            display_topic = display_topic[:77] + "..."

        post_list.insert(
            tk.END,
            f"{post[0]} | {display_topic} | {post[2]}"
        )


root = tk.Tk()

root.title(
    "Social Scheduler"
)

root.geometry(
    "700x500"
)

title = tk.Label(
    root,
    text="SOCIAL SCHEDULER",
    font=("Arial", 20, "bold")
)

title.pack(
    pady=10
)

tk.Label(
    root,
    text="Topic (multiple lines allowed)"
).pack()

topic_entry = tk.Text(
    root,
    width=60,
    height=4
)

topic_entry.pack()

tk.Label(
    root,
    text="Date (YYYY-MM-DD)"
).pack()

date_entry = tk.Entry(
    root,
    width=60
)

date_entry.pack()

tk.Label(
    root,
    text="Time (HH:MM)"
).pack()

time_entry = tk.Entry(
    root,
    width=60
)

time_entry.pack()

tk.Button(
    root,
    text="Schedule Post",
    command=schedule_post
).pack(
    pady=15
)

tk.Label(
    root,
    text="Scheduled Posts"
).pack()

post_list = tk.Listbox(
    root,
    width=100,
    height=15
)

post_list.pack()

load_posts()

root.mainloop()