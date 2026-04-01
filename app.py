from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "library_secret_key"

# ── Replace this with your actual Atlas URI ──────────────────────────────────
MONGO_URI = "mongodb+srv://sajithsid2006_db_user:YSSiXshWMAZu7XWI@cluster0.hp6qqdn.mongodb.net/?appName=Cluster0"

# ─────────────────────────────────────────────────────────────────────────────

client = MongoClient(MONGO_URI)
db     = client["library_db"]
books  = db["books"]


# ── Helper ───────────────────────────────────────────────────────────────────
def get_stats():
    total     = books.count_documents({})
    available = books.count_documents({"status": "available"})
    issued    = books.count_documents({"status": "issued"})
    return {"total": total, "available": available, "issued": issued}


# ── Routes ───────────────────────────────────────────────────────────────────

# READ — home page
@app.route("/")
def index():
    query      = request.args.get("q", "").strip()
    filter_status = request.args.get("filter", "all")

    search = {}
    if query:
        search["$or"] = [
            {"title":  {"$regex": query, "$options": "i"}},
            {"author": {"$regex": query, "$options": "i"}},
            {"isbn":   {"$regex": query, "$options": "i"}},
        ]
    if filter_status in ("available", "issued"):
        search["status"] = filter_status

    all_books = list(books.find(search))
    stats     = get_stats()
    return render_template("index.html",
                           books=all_books,
                           stats=stats,
                           query=query,
                           filter_status=filter_status)


# CREATE — show form
@app.route("/add")
def add_form():
    return render_template("add_book.html")


# CREATE — handle submit
@app.route("/add", methods=["POST"])
def add_book():
    title  = request.form.get("title",  "").strip()
    author = request.form.get("author", "").strip()
    isbn   = request.form.get("isbn",   "").strip()
    genre  = request.form.get("genre",  "").strip()

    if not title or not author or not isbn:
        flash("Title, Author and ISBN are required.", "error")
        return redirect(url_for("add_form"))

    if books.find_one({"isbn": isbn}):
        flash(f'A book with ISBN "{isbn}" already exists.', "error")
        return redirect(url_for("add_form"))

    books.insert_one({
        "title":  title,
        "author": author,
        "isbn":   isbn,
        "genre":  genre,
        "status": "available"
    })
    flash(f'"{title}" added successfully!', "success")
    return redirect(url_for("index"))


# UPDATE — issue a book
@app.route("/issue/<isbn>")
def issue_book(isbn):
    book = books.find_one({"isbn": isbn})
    if book and book["status"] == "available":
        books.update_one({"isbn": isbn}, {"$set": {"status": "issued"}})
        flash(f'"{book["title"]}" has been issued.', "success")
    return redirect(url_for("index"))


# UPDATE — return a book
@app.route("/return/<isbn>")
def return_book(isbn):
    book = books.find_one({"isbn": isbn})
    if book and book["status"] == "issued":
        books.update_one({"isbn": isbn}, {"$set": {"status": "available"}})
        flash(f'"{book["title"]}" has been returned.', "success")
    return redirect(url_for("index"))


# DELETE — remove a book
@app.route("/delete/<isbn>")
def delete_book(isbn):
    book = books.find_one({"isbn": isbn})
    if book:
        books.delete_one({"isbn": isbn})
        flash(f'"{book["title"]}" has been deleted.', "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
