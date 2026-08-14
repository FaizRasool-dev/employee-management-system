CREATE TABLE employees (
    employee_id NUMBER PRIMARY KEY,
    first_name VARCHAR2(50) NOT NULL,
    last_name VARCHAR2(50),
    email VARCHAR2(100) UNIQUE,
    phone VARCHAR2(20),
    department VARCHAR2(50),
    salary NUMBER(12, 2),
    hire_date DATE DEFAULT SYSDATE
);

CREATE SEQUENCE employees_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE OR REPLACE TRIGGER employees_bi
BEFORE INSERT ON employees
FOR EACH ROW
BEGIN
    IF :NEW.employee_id IS NULL THEN
        SELECT employees_seq.NEXTVAL
        INTO :NEW.employee_id
        FROM dual;
    END IF;
END;
/