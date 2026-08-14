from flask import Flask, render_template, request, flash, redirect, url_for
from database.db import get_connection
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test-db")
def test_db():
    try:
        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")

        count = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return f"Database connected successfully! Employees: {count}"

    except Exception as error:
        return f"Database connection failed: {error}"


@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():

    if request.method == "POST":

        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        salary = request.form.get("salary", "").strip()
        hire_date = request.form.get("hire_date", "").strip()

        # Backend validation
        if not first_name or not last_name:
            flash("First name and last name are required.", "danger")
            return render_template("add_employee.html")

        if len(first_name) < 2 or len(last_name) < 2:
            flash("Name must contain at least 2 characters.", "danger")
            return render_template("add_employee.html")

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template("add_employee.html")

        try:
            salary_value = float(salary)

            if salary_value < 0:
                flash("Salary cannot be negative.", "danger")
                return render_template("add_employee.html")

        except ValueError:
            flash("Please enter a valid salary.", "danger")
            return render_template("add_employee.html")

        if not hire_date:
            flash("Hire date is required.", "danger")
            return render_template("add_employee.html")

        connection = get_connection()
        cursor = connection.cursor()

        try:

            sql = """
                INSERT INTO employees
                (
                    first_name,
                    last_name,
                    email,
                    phone,
                    department,
                    salary,
                    hire_date
                )
                VALUES
                (
                    :first_name,
                    :last_name,
                    :email,
                    :phone,
                    :department,
                    :salary,
                    TO_DATE(:hire_date, 'YYYY-MM-DD')
                )
            """

            cursor.execute(
                sql,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                department=department,
                salary=salary_value,
                hire_date=hire_date
            )

            connection.commit()

            flash("Employee added successfully!", "success")

        except Exception as e:

            connection.rollback()

            # Duplicate email
            if "ORA-00001" in str(e):
                flash("This email is already registered.", "danger")
            else:
                flash("Unable to add employee. Please try again.", "danger")

        finally:

            cursor.close()
            connection.close()

        return render_template("add_employee.html")

    return render_template("add_employee.html")

@app.route("/employees")
def employees():

    search = request.args.get("search", "").strip()

    connection = get_connection()
    cursor = connection.cursor()

    if search:

        search_value = f"%{search}%"

        cursor.execute("""
            SELECT employee_id,
                   first_name,
                   last_name,
                   email,
                   phone,
                   department,
                   salary,
                   hire_date
            FROM employees
            WHERE LOWER(first_name) LIKE LOWER(:search_value)
               OR LOWER(last_name) LIKE LOWER(:search_value)
               OR LOWER(email) LIKE LOWER(:search_value)
               OR LOWER(phone) LIKE LOWER(:search_value)
               OR LOWER(department) LIKE LOWER(:search_value)
            ORDER BY employee_id
        """, search_value=search_value)

    else:

        cursor.execute("""
            SELECT employee_id,
                   first_name,
                   last_name,
                   email,
                   phone,
                   department,
                   salary,
                   hire_date
            FROM employees
            ORDER BY employee_id
        """)

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "employees.html",
        employees=employees,
        search=search
    )

@app.route("/edit-employee/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        salary = request.form.get("salary", "").strip()
        hire_date = request.form.get("hire_date", "").strip()

        # Backend validation

        if not first_name or not last_name:
            flash("First name and last name are required.", "danger")

            cursor.close()
            connection.close()

            return redirect(url_for("edit_employee",
                                    employee_id=employee_id))

        if len(first_name) < 2 or len(last_name) < 2:
            flash("Name must contain at least 2 characters.", "danger")

            cursor.close()
            connection.close()

            return redirect(url_for("edit_employee",
                                    employee_id=employee_id))

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "danger")

            cursor.close()
            connection.close()

            return redirect(url_for("edit_employee",
                                    employee_id=employee_id))

        try:
            salary_value = float(salary)

            if salary_value < 0:
                flash("Salary cannot be negative.", "danger")

                cursor.close()
                connection.close()

                return redirect(url_for("edit_employee",
                                        employee_id=employee_id))

        except ValueError:

            flash("Please enter a valid salary.", "danger")

            cursor.close()
            connection.close()

            return redirect(url_for("edit_employee",
                                    employee_id=employee_id))

        if not hire_date:
            flash("Hire date is required.", "danger")

            cursor.close()
            connection.close()

            return redirect(url_for("edit_employee",
                                    employee_id=employee_id))

        try:

            cursor.execute("""
                UPDATE employees
                SET first_name = :first_name,
                    last_name = :last_name,
                    email = :email,
                    phone = :phone,
                    department = :department,
                    salary = :salary,
                    hire_date = TO_DATE(:hire_date, 'YYYY-MM-DD')
                WHERE employee_id = :employee_id
            """,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            salary=salary_value,
            hire_date=hire_date,
            employee_id=employee_id)

            connection.commit()

            flash("Employee updated successfully!", "success")

        except Exception as e:

            connection.rollback()

            if "ORA-00001" in str(e):
                flash("This email is already registered.", "danger")
            else:
                flash("Unable to update employee. Please try again.", "danger")

        finally:

            cursor.close()
            connection.close()

        return redirect(url_for("employees"))

    # GET request

    cursor.execute("""
        SELECT employee_id,
               first_name,
               last_name,
               email,
               phone,
               department,
               salary,
               hire_date
        FROM employees
        WHERE employee_id = :employee_id
    """, employee_id=employee_id)

    employee = cursor.fetchone()

    cursor.close()
    connection.close()

    if employee is None:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))

    return render_template(
        "edit_employee.html",
        employee=employee
    )

@app.route("/delete-employee/<int:employee_id>")
def delete_employee(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE employee_id = :employee_id
    """, employee_id=employee_id)

    connection.commit()

    cursor.close()
    connection.close()

    flash("Employee deleted successfully!", "success")

    return redirect(url_for("employees"))

if __name__ == "__main__":
    app.run(debug=True)