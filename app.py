from flask import Flask, render_template, request, redirect, url_for, send_file
import MySQLdb
from dotenv import load_dotenv
from openai import OpenAI
import os
import csv
from io import StringIO

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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates SQL queries or summarizes text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
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
        comment = request.form['comment']

        # Insert data into MySQL
        db = get_db_connection()
        cursor = db.cursor()
        query = "INSERT INTO data (name, age, email, comment) VALUES (%s, %s, %s, %s)"
        values = (name, age, email, comment)
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
        
        prompt = f"Translate the following natural language question into a SQL query for MySQL. The query should be for the 'data' table with columns 'name', 'age', 'email', and 'comment'. Only return the SQL query, nothing else:\n\n{question}"
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

@app.route('/summarize_comments')
def summarize_comments():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT comment FROM data")
    comments = cursor.fetchall()
    cursor.close()
    db.close()

    all_comments = "***".join([comment[0] for comment in comments if comment[0]])
    
    prompt = f"Do not show the SQL prompt, or even mention it here. Submit your answer formatted in html, where the parts are separated by a horizontal line. You are given a string of comments from people, each comment separated by '***'. Do the following. *Part 1*: list each comment, followed by a setiment analysis rating from -10 to 10, *Part 2*: summarize the string of comments, *Part 3*: give the average sentiment git\n\n{all_comments}"
    summary = chat_with_gpt(prompt)

    return render_template('summary.html', summary=summary)

# This route is meant to download the survey and clear the data
# it is not working, so I'll get back to it later.
# @app.route('/export_data')
# def export_data():
#     # Fetch data from the MySQL table
#     db = get_db_connection()
#     cursor = db.cursor()
#     cursor.execute("SELECT * FROM data")  # Replace 'data' with your table name
#     rows = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]  # Get column headers

#     # Create an in-memory CSV file
#     output = StringIO()
#     writer = csv.writer(output)

#     # Write the column headers first
#     writer.writerow(columns)

#     # Write the data rows
#     for row in rows:
#         writer.writerow(row)

#     # Save the CSV data to the file system if you need it to persist
#     with open("survey_data.csv", "w") as f:
#         f.write(output.getvalue())

#     # Clear the table (only do this if you're sure you want to delete all data)
#     cursor.execute("TRUNCATE TABLE data")
#     db.commit()
#     cursor.close()
#     db.close()

#     # Send the CSV file to the user as a downloadable file
#     output.seek(0)
#     return send_file(
#         StringIO(output.getvalue()),
#         mimetype="text/csv",
#         as_attachment=True,
#         attachment_filename="survey_data.csv"
#     )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)