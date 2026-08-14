from flask import Flask, render_template, request, flash, redirect, url_for
from database.db import get_connection
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")


@app.route("/")
def home():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Total Employees
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]

        # Total Departments
        cursor.execute("""
            SELECT COUNT(DISTINCT department)
            FROM employees
            WHERE department IS NOT NULL
        """)
        total_departments = cursor.fetchone()[0]

        # Average Salary
        cursor.execute("""
            SELECT NVL(AVG(salary), 0)
            FROM employees
        """)
        average_salary = cursor.fetchone()[0]

        return render_template(
            "index.html",
            total_employees=total_employees,
            total_departments=total_departments,
            average_salary=average_salary
        )

    except Exception as e:
        flash("Unable to load dashboard data.", "danger")

        return render_template(
            "index.html",
            total_employees=0,
            total_departments=0,
            average_salary=0
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


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
    department = request.args.get("department", "").strip()

    # Current page
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    if page < 1:
        page = 1

    # Employees per page
    per_page = 10

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Get departments for dropdown
        cursor.execute("""
            SELECT DISTINCT department
            FROM employees
            WHERE department IS NOT NULL
            ORDER BY department
        """)

        departments = [row[0] for row in cursor.fetchall()]

        # Base WHERE condition
        where_clause = "WHERE 1 = 1"
        params = {}

        # Search filter
        if search:
            where_clause += """
                AND (
                    LOWER(first_name) LIKE LOWER(:search)
                    OR LOWER(last_name) LIKE LOWER(:search)
                    OR LOWER(email) LIKE LOWER(:search)
                    OR LOWER(phone) LIKE LOWER(:search)
                    OR LOWER(department) LIKE LOWER(:search)
                )
            """

            params["search"] = f"%{search}%"

        # Department filter
        if department:
            where_clause += """
                AND LOWER(department) = LOWER(:department)
            """

            params["department"] = department

        # Total matching employees
        count_query = f"""
            SELECT COUNT(*)
            FROM employees
            {where_clause}
        """

        cursor.execute(count_query, params)

        total_employees = cursor.fetchone()[0]

        # Calculate total pages
        total_pages = max(
            1,
            (total_employees + per_page - 1) // per_page
        )

        # If page is greater than total pages
        if page > total_pages:
            page = total_pages

        # Calculate offset
        offset = (page - 1) * per_page

        # Get employees for current page
        start_row = offset + 1
        end_row = offset + per_page

        query = f"""
                SELECT employee_id,
                    first_name,
                    last_name,
                    email,
                    phone,
                    department,
                    salary,
                    hire_date
                FROM (
                SELECT employee_id,
                    first_name,
                    last_name,
                    email,
                    phone,
                    department,
                    salary,
                    hire_date,
                    ROW_NUMBER() OVER (ORDER BY employee_id) AS row_num
                FROM employees
                {where_clause}
            )
            WHERE row_num BETWEEN :start_row AND :end_row
        """

        params["start_row"] = start_row
        params["end_row"] = end_row

        cursor.execute(query, params)

        employees = cursor.fetchall()

        return render_template(
            "employees.html",
            employees=employees,
            search=search,
            department=department,
            departments=departments,
            result_count=total_employees,
            page=page,
            total_pages=total_pages
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

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

@app.route("/delete-employee/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM employees
            WHERE employee_id = :employee_id
        """, employee_id=employee_id)

        connection.commit()

        flash("Employee deleted successfully!", "success")

    except Exception as e:
        if connection:
            connection.rollback()

        flash("Unable to delete employee. Please try again.", "danger")

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

    return redirect(url_for("employees"))

@app.route("/employee/<int:employee_id>")
def employee_details(employee_id):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

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

        if employee is None:
            flash("Employee not found.", "danger")
            return redirect(url_for("employees"))

        return render_template(
            "employee_details.html",
            employee=employee
        )

    except Exception:
        flash("Unable to load employee details.", "danger")
        return redirect(url_for("employees"))

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

if __name__ == "__main__":
    app.run(debug=True)