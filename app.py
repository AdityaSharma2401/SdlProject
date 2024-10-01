from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Create a global variable to hold selected students
selected_students = None

TELEGRAM_BOT_TOKEN = '7435441228:AAFd3TztqJjtCkH8NKvEeb-0wTB9wfBoTZw'
BASE_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def send_telegram_message(chat_id, text):
    url = f'{BASE_URL}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'  
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print(f"Message sent to {chat_id}: {text}")
    else:
        print(f"Failed to send message to {chat_id}: {response.text}")

@app.route('/', methods=['GET', 'POST'])
def index():
    global selected_students 
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected!', 'error')
            return redirect(request.url)

        attendance_df = pd.read_excel(file)

        # Process the attendance data
        attendance_df.columns = attendance_df.iloc[3]  
        attendance_df = attendance_df[4:]  

        if 'Total Percentage' in attendance_df.columns:
            attendance_df['Total Percentage'] = pd.to_numeric(attendance_df['Total Percentage'], errors='coerce')
            selected_students = attendance_df[attendance_df['Total Percentage'] < 60]

            return render_template('index.html', tables=[selected_students.to_html(classes='data')], titles=selected_students.columns.values)
        else:
            flash('Total Percentage column is missing in the file!', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/upload_student_data', methods=['GET', 'POST'])
def upload_student_data():
    global selected_students  
    if request.method == 'POST':
        parent_file = request.files['parent_file']
        if not parent_file:
            flash('No file selected!', 'error')
            return redirect(request.url)

        parent_df = pd.read_excel(parent_file)

        
        if selected_students is not None and 'Enrollment Number' in selected_students.columns and 'Enrollment Number' in parent_df.columns:
            
            merged_df = selected_students.merge(parent_df, on='Enrollment Number', how='left')

            # Drop rows with NaN values in 'Telegram ID'
            merged_df = merged_df.dropna(subset=['Telegram ID'])

            # Send messages to parents on Telegram
            send_telegram_messages(merged_df)

            return render_template('index.html', tables=[merged_df.to_html(classes='data')], titles=merged_df.columns.values)
        else:
            flash('Enrollment Number column is missing in one of the files!', 'error')
            return redirect(request.url)
    
    return render_template('index.html')


def send_telegram_messages(low_attendance_students):
    for index, student in low_attendance_students.iterrows():
        student_name = student.get('Name', 'Unknown Student')
        parent_telegram_id = student.get('Telegram ID')
        
        # Ensure the parent_telegram_id is valid and not NaN
        if pd.isna(parent_telegram_id):
            print(f"No valid Telegram ID found for {student_name}, skipping...")
            continue  
        
        message = (f"Dear Parent,\n\n"
                   f"This is to inform you that your child {student_name} has low attendance. "
                   "Please ensure they attend classes regularly.")
        
        try:
            send_telegram_message(parent_telegram_id, message)
        except Exception as e:
            print(f"Error sending message to {parent_telegram_id}: {e}")


if __name__ == '__main__':
    app.run(debug=True)
