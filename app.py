from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "supersecretkey"


selected_students = None
merged_df = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global selected_students
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        
        attendance_df = pd.read_excel(file, header=4)

        
        if 'Enrollment Number' in attendance_df.columns and 'Total Percentage' in attendance_df.columns and 'Name' in attendance_df.columns:
            attendance_df['Total Percentage'] = pd.to_numeric(attendance_df['Total Percentage'], errors='coerce')
            
            # Select students with attendance less than 60%
            low_attendance_students = attendance_df[attendance_df['Total Percentage'] < 60]
            low_attendance_students = low_attendance_students[['Enrollment Number', 'Name', 'Total Percentage']]

            
            selected_students = low_attendance_students.dropna()

            
            return render_template('index.html', low_attendance=True, tables=[low_attendance_students.to_html(classes='data')], titles=low_attendance_students.columns.values)
        else:
            flash('Required columns "Enrollment Number", "Total Percentage" or "Name" are missing in the file!', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/upload_parent_data', methods=['POST'])
def upload_parent_data():
    global selected_students, merged_df
    if request.method == 'POST':
        if selected_students is None:
            flash('Please upload the attendance sheet first!', 'error')
            return redirect(url_for('index'))
        
        parent_file = request.files['parent_file']
        if not parent_file:
            flash('No parent file selected!', 'error')
            return redirect(url_for('index'))

        
        parent_df = pd.read_excel(parent_file)

        
        if 'Enrollment Number' in selected_students.columns and 'Enrollment Number' in parent_df.columns:
            merged_df = selected_students.merge(parent_df[['Enrollment Number', 'Parent Email']], on='Enrollment Number', how='left')
            
            
            merged_df = merged_df.dropna(subset=['Parent Email'])

            
            return render_template('index.html', parent_data=True, tables=[merged_df.to_html(classes='data')], titles=merged_df.columns.values)
        else:
            flash('Enrollment Number column is missing in one of the files!', 'error')
            return redirect(url_for('index'))

@app.route('/send_emails', methods=['POST'])
def send_emails_route():
    global merged_df
    if merged_df is None:
        flash('No parent data available. Please upload parent details.', 'error')
        return redirect(url_for('index'))

    
    if 'Enrollment Number' not in merged_df.columns or 'Parent Email' not in merged_df.columns or 'Name' not in merged_df.columns:
        flash('Required columns "Enrollment Number", "Parent Email", or "Name" are missing in the data!', 'error')
        return redirect(url_for('index'))

    # Send emails to parents
    send_emails(merged_df)

    flash('Emails sent successfully to all parents!', 'success')
    return redirect(url_for('index'))

def send_emails(low_attendance_students):
    sender_email = "adishxrmx2401@gmail.com"
    sender_password = "aswf anxs sdrr byds"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    for index, student in low_attendance_students.iterrows():
        student_name = student['Name']
        enrollment_number = student['Enrollment Number']
        parent_email = student['Parent Email']
        total_percentage = student['Total Percentage']

        subject = "Low Attendance Alert"
        body = (f"Dear Parent,\n\n"
                f"This is to inform you that your child {student_name} (Enrollment Number: {enrollment_number}) "
                f"has an attendance of {total_percentage:.2f}% which is below the required 60%.\n"
                f"Please ensure they attend the classes regularly.\n\n"
                f"Thank you.")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = parent_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, parent_email, msg.as_string())
            server.quit()
            print(f"Email sent to {parent_email} for {student_name}")
        except Exception as e:
            print(f"Failed to send email to {parent_email} for {student_name}: {str(e)}")

if __name__ == '_main_':
    app.run(debug=True)