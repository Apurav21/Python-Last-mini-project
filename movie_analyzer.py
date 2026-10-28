import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "movies.csv")
POSTER_DIR = os.path.join(BASE_DIR, "posters")
os.makedirs(POSTER_DIR, exist_ok=True)
poster_photos = []

# ---------------- DATA ----------------
if not os.path.exists(DATA_FILE):
    messagebox.showerror("Missing Dataset", "movies.csv was not found.")
    raise SystemExit

df = pd.read_csv(DATA_FILE)

# ---------------- WINDOW ----------------
root = tk.Tk()
root.title("Movie Dataset Analyzer")
root.geometry("1200x760")
root.minsize(1050, 680)
root.configure(bg="#111827")

# ---------------- STYLE ----------------
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("Treeview",
                background="#1f2937",
                foreground="white",
                fieldbackground="#1f2937",
                rowheight=28,
                font=("Segoe UI", 10))
style.configure("Treeview.Heading",
                background="#374151",
                foreground="white",
                font=("Segoe UI", 10, "bold"))
style.map("Treeview", background=[("selected", "#2563eb")])

# ---------------- HELPERS ----------------
def clear_content():
    for widget in content.winfo_children():
        widget.destroy()

def card(parent, title, value):
    frame = tk.Frame(parent, bg="#1f2937", width=220, height=105)
    frame.pack_propagate(False)
    tk.Label(frame, text=title, bg="#1f2937", fg="#9ca3af",
             font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(14, 3))
    tk.Label(frame, text=value, bg="#1f2937", fg="white",
             font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=16)
    return frame

def make_tree(parent, data):
    frame = tk.Frame(parent, bg="#111827")
    frame.pack(fill="both", expand=True, padx=20, pady=15)

    cols = list(data.columns)
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor="center")

    for _, row in data.iterrows():
        values = [row[col] for col in cols]
        tree.insert("", "end", values=values)

    tree.grid(row=0, column=0, sticky="nsew")
    yscroll.grid(row=0, column=1, sticky="ns")
    xscroll.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    return tree

# ---------------- DASHBOARD ----------------
def dashboard():
    clear_content()

    tk.Label(content, text="Dashboard", bg="#111827", fg="white",
             font=("Segoe UI", 25, "bold")).pack(anchor="w", padx=25, pady=(22, 5))
    tk.Label(content, text="Overview of the movie dataset",
             bg="#111827", fg="#9ca3af",
             font=("Segoe UI", 11)).pack(anchor="w", padx=25)

    stats = tk.Frame(content, bg="#111827")
    stats.pack(fill="x", padx=25, pady=25)

    highest = df.loc[df["Rating"].idxmax(), "Movie"]
    genre = df["Genre"].mode().iloc[0]

    for title, value in [
        ("Total Movies", len(df)),
        ("Average Rating", f"{df['Rating'].mean():.2f}"),
        ("Highest Rating", f"{df['Rating'].max():.1f}"),
        ("Most Common Genre", genre)
    ]:
        card(stats, title, value).pack(side="left", padx=(0, 15))

    box = tk.Frame(content, bg="#1f2937")
    box.pack(fill="x", padx=25, pady=10)

    tk.Label(box, text="🏆 Highest Rated Movie",
             bg="#1f2937", fg="#9ca3af",
             font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(18, 3))
    tk.Label(box, text=highest,
             bg="#1f2937", fg="white",
             font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=20, pady=(0, 18))

    tk.Label(content, text="Quick actions",
             bg="#111827", fg="white",
             font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=25, pady=(20, 8))

    actions = tk.Frame(content, bg="#111827")
    actions.pack(anchor="w", padx=25)

    for text, command in [
        ("Top Rated Movies", top_movies),
        ("Genre Analysis", genre_analysis),
        ("Year Analysis", year_analysis),
        ("Recommendations", recommendations)
    ]:
        tk.Button(actions, text=text, command=command,
                  bg="#2563eb", fg="white", relief="flat",
                  padx=18, pady=10, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))

# ---------------- MOVIE EXPLORER ----------------
def explorer():
    clear_content()

    tk.Label(content, text="Movie Explorer", bg="#111827", fg="white",
             font=("Segoe UI", 25, "bold")).pack(anchor="w", padx=25, pady=(22, 5))

    controls = tk.Frame(content, bg="#111827")
    controls.pack(fill="x", padx=25, pady=15)

    tk.Label(controls, text="Search:", bg="#111827", fg="white").pack(side="left")
    search_var = tk.StringVar()
    search = tk.Entry(controls, textvariable=search_var, width=28,
                      bg="#1f2937", fg="white", insertbackground="white",
                      relief="flat")
    search.pack(side="left", padx=8, ipady=7)

    tk.Label(controls, text="Genre:", bg="#111827", fg="white").pack(side="left", padx=(15, 5))
    genre_var = tk.StringVar(value="All")
    genres = ["All"] + sorted(df["Genre"].unique().tolist())
    genre_box = ttk.Combobox(controls, textvariable=genre_var,
                             values=genres, state="readonly", width=16)
    genre_box.pack(side="left")

    tk.Label(controls, text="Year:", bg="#111827", fg="white").pack(side="left", padx=(15, 5))
    year_var = tk.StringVar(value="All")
    years = ["All"] + [str(y) for y in sorted(df["Year"].unique(), reverse=True)]
    year_box = ttk.Combobox(controls, textvariable=year_var,
                            values=years, state="readonly", width=10)
    year_box.pack(side="left")

    table_holder = tk.Frame(content, bg="#111827")
    table_holder.pack(fill="both", expand=True)

    def refresh(*args):
        result = df.copy()
        q = search_var.get().strip().lower()
        if q:
            result = result[result["Movie"].str.lower().str.contains(q, na=False)]
        if genre_var.get() != "All":
            result = result[result["Genre"] == genre_var.get()]
        if year_var.get() != "All":
            result = result[result["Year"] == int(year_var.get())]

        for w in table_holder.winfo_children():
            w.destroy()
        make_tree(table_holder, result[["Movie", "Genre", "Year", "Rating", "Votes", "Duration"]])

    tk.Button(controls, text="Search / Filter", command=refresh,
              bg="#2563eb", fg="white", relief="flat",
              padx=14, pady=7).pack(side="left", padx=15)

    search.bind("<Return>", refresh)
    genre_box.bind("<<ComboboxSelected>>", refresh)
    year_box.bind("<<ComboboxSelected>>", refresh)
    refresh()

# ---------------- TOP MOVIES ----------------
def top_movies():
    clear_content()
    tk.Label(content, text="Top Rated Movies", bg="#111827", fg="white",
             font=("Segoe UI", 25, "bold")).pack(anchor="w", padx=25, pady=(22, 5))
    top = df.sort_values("Rating", ascending=False).head(10)
    make_tree(content, top[["Movie", "Genre", "Year", "Rating", "Votes"]])

# ---------------- CHART WINDOW IN CONTENT ----------------
def show_chart(title, fig):
    clear_content()
    tk.Label(content, text=title, bg="#111827", fg="white",
             font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=25, pady=15)
    canvas = FigureCanvasTkAgg(fig, master=content)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

# ---------------- ANALYTICS ----------------
def genre_analysis():
    counts = df["Genre"].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    counts.plot(kind="bar", ax=ax)
    ax.set_title("Number of Movies by Genre")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Number of Movies")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    show_chart("Genre Analysis", fig)

def year_analysis():
    counts = df.groupby("Year").size()
    fig, ax = plt.subplots(figsize=(9, 5))
    counts.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Movies Released by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Movies")
    fig.tight_layout()
    show_chart("Year Analysis", fig)

def rating_analysis():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df["Rating"], bins=8)
    ax.set_title("Movie Rating Distribution")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Number of Movies")
    fig.tight_layout()
    show_chart("Rating Analysis", fig)

def votes_analysis():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(df["Votes"], df["Rating"], alpha=0.6)
    ax.set_title("Rating vs Number of Votes")
    ax.set_xlabel("Votes")
    ax.set_ylabel("Rating")
    fig.tight_layout()
    show_chart("Votes vs Rating", fig)

# ---------------- RECOMMENDATIONS ----------------
def recommendations():
    clear_content()

    tk.Label(content, text="Movie Recommendations", bg="#111827", fg="white",
             font=("Segoe UI", 25, "bold")).pack(anchor="w", padx=25, pady=(22, 5))

    controls = tk.Frame(content, bg="#111827")
    controls.pack(anchor="w", padx=25, pady=20)

    tk.Label(controls, text="Genre:", bg="#111827", fg="white").grid(row=0, column=0, padx=5)
    genre_var = tk.StringVar(value="Action")
    combo = ttk.Combobox(controls, textvariable=genre_var,
                         values=sorted(df["Genre"].unique()), state="readonly", width=18)
    combo.grid(row=0, column=1, padx=8)

    tk.Label(controls, text="Minimum Rating:", bg="#111827", fg="white").grid(row=0, column=2, padx=(20, 5))
    rating_var = tk.DoubleVar(value=8.0)
    spin = tk.Spinbox(controls, from_=0, to=10, increment=0.1,
                      textvariable=rating_var, width=8)
    spin.grid(row=0, column=3, padx=8)

    holder = tk.Frame(content, bg="#111827")
    holder.pack(fill="both", expand=True)

    def recommend():
        try:
            minimum = float(rating_var.get())
        except ValueError:
            messagebox.showerror("Invalid Rating", "Enter a number between 0 and 10.")
            return

        result = df[(df["Genre"] == genre_var.get()) &
                    (df["Rating"] >= minimum)].sort_values("Rating", ascending=False).head(10)

        for w in holder.winfo_children():
            w.destroy()

        if result.empty:
            tk.Label(holder, text="No movies match your selection.",
                     bg="#111827", fg="white",
                     font=("Segoe UI", 14)).pack(pady=30)
        else:
            make_tree(holder, result[["Movie", "Genre", "Year", "Rating", "Votes"]])

    tk.Button(controls, text="Recommend", command=recommend,
              bg="#16a34a", fg="white", relief="flat",
              padx=15, pady=7).grid(row=0, column=4, padx=10)
    recommend()



# ---------------- MOVIE POSTER GALLERY ----------------
def safe_poster_name(movie):
    """Match movie titles to Windows-safe poster filenames."""
    return re.sub(r'[<>:"/\\|?*]', "", str(movie)).strip()


def find_poster(movie):
    """Find a locally saved poster such as posters/Inception.jpg."""
    stem = safe_poster_name(movie)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(POSTER_DIR, stem + ext)
        if os.path.isfile(path):
            return path
    return None


def build_poster_image(row, size=(120, 180)):
    """Load a real local image, or draw a placeholder until one is added."""
    path = find_poster(row["Movie"])
    if path:
        try:
            with Image.open(path) as img:
                return ImageOps.fit(img.convert("RGB"), size, method=Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            pass

    image = Image.new("RGB", size, "#263548")
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rectangle((0, int(h * 0.66), w, h), fill="#111827")
    try:
        title_font = ImageFont.truetype("arial.ttf", 22)
        small_font = ImageFont.truetype("arial.ttf", 11)
    except OSError:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    initials = "".join(word[0] for word in str(row["Movie"]).split()[:2]).upper() or "M"
    draw.text((w // 2, int(h * 0.34)), initials, anchor="mm", fill="white", font=title_font)
    draw.text((6, int(h * 0.70)), str(row["Movie"])[:20], fill="white", font=small_font)
    draw.text((6, int(h * 0.82)), str(row.get("Genre", "Movie"))[:18], fill="#cbd5e1", font=small_font)
    draw.text((6, int(h * 0.92)), f"Rating: {float(row.get('Rating', 0)):.1f}", fill="#facc15", font=small_font)
    return image


def open_poster_details(row):
    """Show a selected movie's poster and basic information."""
    window = tk.Toplevel(root)
    window.title(str(row["Movie"]))
    window.geometry("440x440")
    window.configure(bg="#111827")
    photo = ImageTk.PhotoImage(build_poster_image(row, (180, 270)))
    label = tk.Label(window, image=photo, bg="#111827")
    label.image = photo
    label.pack(side="left", padx=20, pady=20)
    details = tk.Frame(window, bg="#111827")
    details.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=22)
    tk.Label(details, text=str(row["Movie"]), bg="#111827", fg="white",
             font=("Segoe UI", 14, "bold"), wraplength=190, justify="left").pack(anchor="w", pady=(0, 12))
    for label_text, value in [
        ("Genre", row.get("Genre", "N/A")),
        ("Year", row.get("Year", "N/A")),
        ("Rating", row.get("Rating", "N/A")),
        ("Votes", row.get("Votes", "N/A")),
        ("Duration", row.get("Duration", "N/A")),
    ]:
        tk.Label(details, text=f"{label_text}: {value}", bg="#111827", fg="#d1d5db",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=3)


def movie_posters():
    """Display all movies in a scrollable poster gallery."""
    global poster_photos
    clear_content()
    poster_photos = []
    tk.Label(content, text="Movie Posters", bg="#111827", fg="white",
             font=("Segoe UI", 25, "bold")).pack(anchor="w", padx=25, pady=(22, 5))
    tk.Label(content,
             text="Put JPG, JPEG, PNG or WEBP files in the posters folder. Filenames must match movie titles.",
             bg="#111827", fg="#9ca3af", font=("Segoe UI", 10), wraplength=850,
             justify="left").pack(anchor="w", padx=25, pady=(0, 10))

    found = sum(1 for movie in df["Movie"] if find_poster(movie))
    tk.Label(content, text=f"Real posters found: {found} / {len(df)}",
             bg="#111827", fg="#60a5fa", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=25)

    wrap = tk.Frame(content, bg="#111827")
    wrap.pack(fill="both", expand=True, padx=20, pady=10)
    canvas = tk.Canvas(wrap, bg="#111827", highlightthickness=0)
    scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    grid = tk.Frame(canvas, bg="#111827")
    canvas_window = canvas.create_window((0, 0), window=grid, anchor="nw")

    def update_scroll(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())
    grid.bind("<Configure>", update_scroll)
    canvas.bind("<Configure>", update_scroll)

    columns = 5
    for index, (_, row) in enumerate(df.iterrows()):
        card = tk.Frame(grid, bg="#1f2937", padx=9, pady=9, width=155, height=270)
        card.grid(row=index // columns, column=index % columns, padx=7, pady=7, sticky="n")
        card.pack_propagate(False)
        image = build_poster_image(row)
        photo = ImageTk.PhotoImage(image)
        poster_photos.append(photo)
        poster_label = tk.Label(card, image=photo, bg="#1f2937", cursor="hand2")
        poster_label.image = photo
        poster_label.pack()
        title = tk.Label(card, text=str(row["Movie"]), bg="#1f2937", fg="white",
                         font=("Segoe UI", 9, "bold"), wraplength=132, justify="center")
        title.pack(pady=(7, 2))
        tk.Label(card, text=f"{row['Year']} · {row['Genre']} · ★ {float(row['Rating']):.1f}",
                 bg="#1f2937", fg="#9ca3af", font=("Segoe UI", 8), wraplength=132).pack()
        for widget in (card, poster_label, title):
            widget.bind("<Button-1>", lambda _e, r=row.copy(): open_poster_details(r))

    # Enable mouse wheel scrolling while the pointer is over the gallery.
    def wheel(event):
        if event.delta:
            canvas.yview_scroll(int(-event.delta / 120), "units")
    canvas.bind_all("<MouseWheel>", wheel)


# ---------------- SIDEBAR ----------------
sidebar = tk.Frame(root, bg="#0b1220", width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="🎬 MOVIE\nANALYZER",
         bg="#0b1220", fg="white",
         font=("Segoe UI", 20, "bold"),
         justify="left").pack(anchor="w", padx=22, pady=25)

def nav_button(text, command):
    tk.Button(sidebar, text=text, command=command,
              bg="#0b1220", fg="#d1d5db",
              activebackground="#1d4ed8", activeforeground="white",
              relief="flat", anchor="w",
              font=("Segoe UI", 11),
              padx=22, pady=12).pack(fill="x")

nav_button("🏠  Dashboard", dashboard)
nav_button("🎥  Movie Explorer", explorer)
nav_button("🖼  Movie Posters", movie_posters)
nav_button("⭐  Top Rated", top_movies)
nav_button("📊  Genre Analysis", genre_analysis)
nav_button("📅  Year Analysis", year_analysis)
nav_button("📈  Rating Analysis", rating_analysis)
nav_button("🔵  Votes vs Rating", votes_analysis)
nav_button("🎯  Recommendations", recommendations)

tk.Label(sidebar, text=f"{len(df)} movies loaded",
         bg="#0b1220", fg="#6b7280",
         font=("Segoe UI", 9)).pack(side="bottom", pady=20)

# ---------------- CONTENT ----------------
content = tk.Frame(root, bg="#111827")
content.pack(side="right", fill="both", expand=True)

dashboard()

root.mainloop()
