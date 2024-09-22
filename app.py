from flask import Flask, render_template, request, redirect, url_for
import MySQLdb
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'carbonjo'
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = 'jc_survey'

# Function to create a MySQL connection
def get_db_connection():
    db = MySQLdb.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        passwd=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB']
    )
    return db

def chat_with_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Use an available model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates SQL queries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def collect_data():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']

        # Insert data into MySQL
        db = get_db_connection()
        cursor = db.cursor()
        query = "INSERT INTO data (name, age, email) VALUES (%s, %s, %s)"
        values = (name, age, email)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('ask_question'))
    return render_template('collect_data.html')

@app.route('/ask', methods=['GET', 'POST'])
def ask_question():
    if request.method == 'POST':
        question = request.form['question']
        
        prompt = f"Translate the following natural language question into a SQL query for MySQL. The query should be for the 'data' table with columns 'name', 'age', and 'email'. Only return the SQL query, nothing else:\n\n{question}"
        sql_query = chat_with_gpt(prompt)
        
        try:
            db = get_db_connection()
            cursor = db.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql_query)
            results = cursor.fetchall()
            cursor.close()
            db.close()

            return render_template('results.html', results=results, query=sql_query, question=question)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('ask_question.html', error=error_message, query=sql_query, question=question)
    return render_template('ask_question.html')

# The block that runs the Flask application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
