from flask import Flask, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_username'
app.config['MYSQL_PASSWORD'] = 'JOMBETA06.!1123'
app.config['MYSQL_DB'] = 'jomtest'

mysql = MySQL(app)

@app.route('/')
def interest_form():
    cur = mysql.connection.cursor()

    # Fetch categories
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    # Fetch interests grouped by category
    interests_by_category = {}
    for category in categories:
        cat_id, cat_name = category
        cur.execute("SELECT name FROM interests WHERE category_id = %s", (cat_id,))
        interests = cur.fetchall()
        interests_by_category[cat_name] = [i[0] for i in interests]

    cur.close()

    return render_template('customise.html', interests_by_category=interests_by_category)
