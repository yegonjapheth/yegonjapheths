from flask import Flask, render_template, request, redirect
import sqlite3
import datetime

app = Flask(__name__)

# Create a connection to the SQLite database
conn = sqlite3.connect('x.db', check_same_thread=False)
conn.row_factory = sqlite3.Row

# Create tables if they don't exist
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        type TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        grade TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS borrowers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        grade INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,  -- New column to store the borrowing date
        return_date TEXT NOT NULL,  -- New column to store the return date
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
''')

conn.commit()

def book_is_available(book_id):
    c = conn.cursor()
    c.execute('SELECT COUNT(id) FROM borrowers WHERE book_id = ?', (book_id,))
    count = c.fetchone()[0]
    return count == 0

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/books')
def display_books():
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    return render_template('books.html', books=books, book_is_available=book_is_available)


@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        grade = request.form['grade']
        
        c = conn.cursor()
        c.execute('INSERT INTO members (name, grade) VALUES (?, ?)', (name, grade))
        conn.commit()

        return redirect('/members')

    return render_template('add_member.html')


@app.route('/members')
def display_members():
    c = conn.cursor()
    c.execute('SELECT * FROM members')
    members = c.fetchall()
    return render_template('members.html', members=members)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        book_type = request.form['type']

        c = conn.cursor()
        c.execute('INSERT INTO books (title, author, type) VALUES (?, ?, ?)', (title, author, book_type))
        conn.commit()

        return redirect('/books')
    
    return render_template('add_book.html')


@app.route('/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    if request.method == 'POST':
        name = request.form['name']
        grade = request.form['grade']
        book_id = request.form['book_id']
        today = datetime.datetime.today()
        return_date = today + datetime.timedelta(days=14)

        c = conn.cursor()

        # Check if the book ID exists in the books table
        c.execute('SELECT id FROM books WHERE id = ?', (book_id,))
        book = c.fetchone()

        if book:
            c.execute('INSERT INTO borrowers (name, grade, book_id, borrow_date, return_date) VALUES (?, ?, ?, ?, ?)',
                      (name, grade, book_id, today.strftime('%Y-%m-%d'), return_date.strftime('%Y-%m-%d')))
            conn.commit()
            return redirect('/borrowed_books')
        else:
            error_message = "Invalid Book ID. Please enter a valid Book ID."
            return render_template('borrow_book.html', error_message=error_message)

    return render_template('borrow_book.html')


@app.route('/borrowed_books')
def display_borrowed_books():
    c = conn.cursor()
    c.execute('''
        SELECT books.title, books.author, members.name AS borrower_name, borrowers.borrow_date, borrowers.return_date
        FROM books
        INNER JOIN borrowers ON books.id = borrowers.book_id
        INNER JOIN members ON borrowers.name = members.name
    ''')
    borrowed_books = c.fetchall()
    return render_template('borrowed_books.html', borrowed_books=borrowed_books)

@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        borrower_id = request.form['borrower_id']

        c = conn.cursor()
        # Check if the borrower ID exists in the borrowers table
        c.execute('SELECT id FROM borrowers WHERE id = ?', (borrower_id,))
        borrower = c.fetchone()

        if borrower:
            # Fetch the book ID and update the book status
            c.execute('SELECT book_id FROM borrowers WHERE id = ?', (borrower_id,))
            book_id = c.fetchone()[0]

            # Update the book status to available
            c.execute('DELETE FROM borrowers WHERE id = ?', (borrower_id,))
            conn.commit()

            return redirect('/borrowed_books')
        else:
            error_message = "Invalid Borrower ID. Please enter a valid Borrower ID."
            return render_template('return_book.html', error_message=error_message)

    return render_template('return_book.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
