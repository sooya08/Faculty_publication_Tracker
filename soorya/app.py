from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from datetime import datetime
from flask_mail import Mail, Message
import re
import mysql.connector
import logging
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# PDF upload config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Soorya@0213",
    database="faculty1"
)
cursor = db.cursor()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'Sooryas851@gmail.com'
app.config['MAIL_PASSWORD'] = 'otcx iari owdk mnub'  # Replace with new Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'Sooryas851@gmail.com'

mail = Mail(app)

# Login required decorator
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# Admin required decorator
def admin_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'Admin':
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    return render_template('new.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=session.get('username'), user_type=session.get('user_type'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']

    select_query = "SELECT * FROM users WHERE username = %s AND password = %s AND user_type = %s"
    cursor.execute(select_query, (username, password, user_type))
    user = cursor.fetchone()

    if user:
        if user_type == 'Faculty' and user[5] == 0:  # Check approved status (index 5 is approved column)
            flash('Your Faculty account is pending admin approval.', 'error')
            return redirect(url_for('login_page'))
        session['username'] = username
        session['user_type'] = user_type
        return redirect(url_for('home'))
    else:
        flash('Invalid credentials. Please try again or sign up.', 'error')
        return redirect(url_for('login_page'))

@app.route('/adminlogin')
def adminlogin():
    return render_template('adminlogin.html')

@app.route('/adminlogin1', methods=['POST'])
def adminlogin1():
    username = request.form['username']
    password = request.form['password']

    if username == 'admin' and password == 'admin123':
        session['username'] = username
        session['user_type'] = 'Admin'
        return redirect(url_for('admin_approval'))
    else:
        flash('Invalid admin credentials. Please try again.', 'error')
        return redirect(url_for('adminlogin'))

@app.route('/signup_submit', methods=['POST'])
def signup_submit():
    error = None
    success = None
    username = request.form['username'].strip()
    email = request.form.get('email', '').strip()  # Email is optional for Faculty
    password = request.form['password'].strip()
    user_type = request.form['user_type']

    # Validate username
    if not username:
        error = 'Username is required'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)
    if not re.search('[a-zA-Z]', username):
        error = 'Username must contain at least one alphabetic letter'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)

    # Validate password
    if not password:
        error = 'Password is required'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)
    if len(password) < 6:
        error = 'Password must be at least 6 characters long'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)

    # Validate email for Students
    if user_type == 'Student':
        if not email:
            error = 'Email is required for Students'
            return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            error = 'Invalid email format'
            return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)

    # Check for existing username or email (if provided)
    if email:
        cursor.execute("SELECT * FROM users WHERE username = %s OR (email = %s AND email IS NOT NULL)", (username, email))
    else:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        error = 'Username or email already taken'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)

    # Set approved status: 1 for Student, 0 for Faculty (pending)
    approved = 1 if user_type == 'Student' else 0
    insert_query = "INSERT INTO users (username, email, password, user_type, approved) VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(insert_query, (username, email or None, password, user_type, approved))
        db.commit()
    except mysql.connector.Error as err:
        error = f'Database error: {str(err)}'
        return render_template('signup.html', error=error, username=username, email=email, user_type=user_type)

    if user_type == 'Student':
        success = 'Student account created successfully! Please log in.'
        return render_template('login.html', success=success)
    else:
        success = 'Faculty account created. Awaiting admin approval.'
        return render_template('login.html', success=success)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))

@app.route('/submitpublication')
@login_required
def submitpublication():
    return render_template('submit.html', user_type=session.get('user_type'))

@app.route('/submit', methods=['GET', 'POST'])

@login_required
def submit():
    if request.method == 'POST':
        pdf_filename = None
        if 'publication_pdf' in request.files:
            file = request.files['publication_pdf']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                pdf_filename = filename

        data = (
            request.form['faculty_name'],
            request.form['department'],
            request.form['title'],
            request.form['pub_type'],
            request.form['publisher'],
            request.form['publisher_email'],
            request.form['publication_year'],
            request.form['doi_or_link'],
            pdf_filename
        )
        cursor.execute("""
            INSERT INTO publications 
            (faculty_name, department, title, pub_type, publisher, publisher_email, publication_year, doi_or_link, pdf_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        db.commit()

        # Fetch all Student recipients (regardless of approved status)
        cursor.execute("SELECT email FROM users WHERE user_type = 'Student' AND email IS NOT NULL")
        recipients = [row[0] for row in cursor.fetchall()]
        logger.debug(f"Student recipients for publication notification: {recipients}")

        if recipients:
            msg = Message(
                subject=f"New Publication: {data[2]}",
                sender=app.config['MAIL_USERNAME'],
                recipients=recipients
            )
            msg.body = f"A new publication has been submitted:\n\nTitle: {data[2]}\nFaculty: {data[0]}\nDepartment: {data[1]}\nType: {data[3]}\nPublisher: {data[4]}\nYear: {data[6]}\nDOI/Link: {data[7] or 'N/A'}\n\nCheck the publication tracker for details."
            try:
                mail.send(msg)
                logger.debug("Publication notification email sent successfully to Students")
                flash('Publication submitted successfully!', 'success')
            except Exception as e:
                logger.error(f"Error sending publication notification emails to Students: {str(e)}")
                flash(f'Error sending notification emails to Students: {str(e)}', 'error')
        else:
            logger.warning("No Student recipients with valid emails found for publication notification")
            flash('Publication submitted, but no Student recipients with valid emails found.', 'error')

        return redirect(url_for('view_publications'))
    return render_template('submit.html', user_type=session.get('user_type'))
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/share_notes', methods=['GET', 'POST'])
@login_required
def share_notes():
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # Fetch all Student recipients (regardless of approved status)
        cursor.execute("SELECT email FROM users WHERE user_type = 'Student' AND email IS NOT NULL")
        recipients = [row[0] for row in cursor.fetchall()]
        logger.debug(f"Student recipients for notes notification: {recipients}")

        if recipients:
            msg = Message(
                subject=f"New Notes: {title}",
                sender=app.config['MAIL_USERNAME'],
                recipients=recipients
            )
            msg.body = f"New notes have been shared by {session.get('username')}:\n\nTitle: {title}\nContent: {content}\n\nCheck the publication tracker for details."
            try:
                mail.send(msg)
                logger.debug("Notes notification email sent successfully to Students")
                flash('Notes shared successfully!', 'success')
            except Exception as e:
                logger.error(f"Error sending notes notification emails to Students: {str(e)}")
                flash(f'Error sending notification emails to Students: {str(e)}', 'error')
        else:
            logger.warning("No Student recipients with valid emails found for notes notification")
            flash('Notes shared, but no Student recipients with valid emails found.', 'error')

        return redirect(url_for('home'))
    return render_template('share_notes.html', user_type=session.get('user_type'))

@app.route('/view_publications')
@login_required
def view_publications():
    faculty = request.args.get('faculty', '').strip()
    pub_type = request.args.get('type', '').strip()
    year = request.args.get('year', '').strip()

    query = "SELECT * FROM publications WHERE 1=1"
    params = []
    if faculty:
        query += " AND faculty_name LIKE %s"
        params.append(f"%{faculty}%")
    if pub_type:
        query += " AND pub_type LIKE %s"
        params.append(f"%{pub_type}%")
    if year:
        query += " AND publication_year LIKE %s"
        params.append(f"%{year}%")

    cursor.execute(query, params)
    records = cursor.fetchall()
    return render_template('view.html', records=records, user_type=session.get('user_type'))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %b %Y, %I:%M %p'):
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return value.strftime(format)

@app.route('/admin')
@login_required
@admin_required
def admin():
    cursor.execute("SELECT * FROM publications")
    records = cursor.fetchall()
    return render_template('admin.html', records=records, user_type=session.get('user_type'))

@app.route('/admin_approval')
@admin_required
def admin_approval():
    cursor.execute("SELECT id, username, email, user_type, created_at FROM users WHERE user_type = 'Faculty' AND approved = 0")
    pending_users = cursor.fetchall()
    return render_template('admin_approval.html', pending_users=pending_users)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    cursor.execute("UPDATE users SET approved = 1 WHERE id = %s", (user_id,))
    db.commit()
    flash('Faculty account approved successfully!', 'success')
    return redirect(url_for('admin_approval'))

@app.route('/reject_user/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    flash('Faculty account request rejected.', 'success')
    return redirect(url_for('admin_approval'))

@app.route('/send_remark', methods=['POST'])
@login_required
def send_remark():
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    sender_gmail = request.form['sender_gmail']
    publisher_email = request.form['publisher_email']
    remark = request.form['remark']
    title = request.form['title']

    msg = Message(
        subject=f"Remark on Publication: {title}",
        sender=app.config['MAIL_USERNAME'],
        recipients=[publisher_email]
    )
    msg.body = f"From: {sender_gmail}\n\nHere is a remark regarding the publication titled '{title}':\n\n{remark}\n\nRegards,\n{sender_gmail}"

    try:
        mail.send(msg)
        logger.debug("Remark email sent successfully")
        flash('Remark sent successfully!', 'success')
    except Exception as e:
        logger.error(f"Error sending remark email: {str(e)}")
        flash(f'Error sending email: {str(e)}', 'error')
    return redirect(url_for('admin'))

@app.route('/edit/<int:pub_id>', methods=['GET'])
@login_required
@admin_required
def edit_publication(pub_id):
    cursor.execute("SELECT * FROM publications WHERE pub_id = %s", (pub_id,))
    record = cursor.fetchone()
    return render_template('edit_publication.html', record=record, user_type=session.get('user_type'))

@app.route('/update/<int:pub_id>', methods=['POST'])
@login_required
@admin_required
def update_publication(pub_id):
    faculty = request.form['faculty']
    department = request.form['department']
    title = request.form['title']
    type_ = request.form['type']
    publisher = request.form['publisher']
    publisher_email = request.form['publisher_email']
    year = request.form['year']
    link = request.form['link']
    
    cursor.execute("""
        UPDATE publications 
        SET faculty_name=%s, department=%s, title=%s, pub_type=%s, publisher=%s, publisher_email=%s, publication_year=%s, doi_or_link=%s 
        WHERE pub_id=%s
    """, (faculty, department, title, type_, publisher, publisher_email, year, link, pub_id))
    db.commit()
    flash('Publication updated successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete/<int:pub_id>', methods=['POST'])
@login_required
@admin_required
def delete_publication(pub_id):
    cursor.execute("DELETE FROM publications WHERE pub_id = %s", (pub_id,))
    db.commit()
    flash('Publication deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/view')
@login_required
def view():
    return redirect(url_for('view_publications'))

@app.route('/test_email')
@login_required
@admin_required
def test_email():
    cursor.execute("SELECT email FROM users WHERE user_type = 'Student' AND email IS NOT NULL")
    recipients = [row[0] for row in cursor.fetchall()]
    logger.debug(f"Test email recipients (Students): {recipients}")

    if recipients:
        msg = Message(
            subject="Test Email from Faculty Publication Tracker",
            sender=app.config['MAIL_USERNAME'],
            recipients=recipients
        )
        msg.body = "This is a test email to verify email functionality for Students."
        try:
            mail.send(msg)
            logger.debug("Test email sent successfully to Students")
            flash('Test email sent successfully to Students!', 'success')
        except Exception as e:
            logger.error(f"Error sending test email to Students: {str(e)}")
            flash(f'Error sending test email to Students: {str(e)}', 'error')
    else:
        logger.warning("No Student recipients with valid emails found for test email")
        flash('No Student recipients with valid emails found for test email.', 'error')

    return redirect(url_for('admin_approval'))

if __name__ == '__main__':
    app.run(debug=True)