import streamlit as st
import psycopg2
import pandas as pd

def get_id_sys_date_load(sys_date_load):
    cur.execute('''
        SELECT "id_sysPersonLoad"
        FROM "sysPersonsLoad"
        WHERE "sysDateLoad" = %s
    ''', (sys_date_load,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None

# Initialize connection.
conn = psycopg2.connect(
    dbname="denis",
    user="denis",
    password="denis",
    host="localhost",
    port="5431"
)

# Create a cursor object.
cur = conn.cursor()

# Perform queries.
cur.execute('''
    SELECT o.id_order, o.id_sale, o.id_customers, o.id_restaurant, o.id_employee, o.cheque, o."id_sysDateLoad", o."sysDateLoad",
           c."FirstName", c."LastName", c."Email", c."Address", c.id_city, c.id_region, c."Phone", c."Birthday", c."FavoriteDish",
           r.name_city, r.name_street, r.house,
           e."name_employee", e.id_timetable, e.salary,
           s."name_sale", s."procentSale",
           sp."sysPersonName", sp."sysStatus"
    FROM orders o
    JOIN сustomers c ON o.id_customers = c.id_сustomers
    JOIN restaurants r ON o.id_restaurant = r.id_restaurant
    JOIN employee e ON o.id_employee = e.id_employee
    JOIN sales s ON o.id_sale = s.id_sale
    JOIN "sysPersonsLoad" sp ON o."id_sysDateLoad" = sp."id_sysPersonLoad"
''')

# Fetch all rows from the result.
rows = cur.fetchall()

# Create a DataFrame from the fetched rows.
df_orders = pd.DataFrame(rows, columns=[desc[0] for desc in cur.description])

# Display results.
st.subheader("Orders Table:")

# Compact representation of orders table
st.write(df_orders)

# Add functionality to insert new rows into the orders table
st.subheader("Add New Order")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    order_id = st.text_input("Order ID")
    sale_id = st.text_input("Sale ID")
    customer_id = st.text_input("Customer ID")

with col2:
    restaurant_id = st.text_input("Restaurant ID")
    employee_id = st.text_input("Employee ID")
    cheque = st.text_input("Cheque")

with col3:
    sys_date_load = st.date_input("SysDateLoad", value=pd.Timestamp("today"))

if st.button("Add Order"):
    # Check if the id_sysDateLoad exists in sysPersonsLoad table
    cur.execute(f'''
        SELECT EXISTS (
            SELECT 1
            FROM "sysPersonsLoad"
            WHERE "sysDateLoad" = %s
        );
    ''', (sys_date_load,))
    sys_date_load_exists = cur.fetchone()[0]

    if not sys_date_load_exists:
        # Get the maximum id_sysPersonLoad from sysPersonsLoad table
        cur.execute('SELECT MAX("id_sysPersonLoad") FROM "sysPersonsLoad";')
        max_sys_person_load = cur.fetchone()[0]
        new_sys_person_load_id = max_sys_person_load + 1 if max_sys_person_load is not None else 1

        # Insert new sysDateLoad into sysPersonsLoad table
        cur.execute(f'''
            INSERT INTO "sysPersonsLoad" ("id_sysPersonLoad", "sysPersonName", "sysStatus", "sysDateLoad") 
            VALUES (%s, 'New Date', 'New Status', %s)
        ''', (new_sys_person_load_id, sys_date_load))
        st.success(f"New sysDateLoad '{sys_date_load}' added to sysPersonsLoad table!")
    else:
        # Получите id_sysDateLoad для данной даты
        id_sys_date_load = get_id_sys_date_load(sys_date_load)

        if id_sys_date_load is not None:
            # Get the maximum order ID from the existing orders
            cur.execute('SELECT MAX("id_order") FROM "orders";')
            max_order_id = cur.fetchone()[0]
            new_order_id = max_order_id + 1

            # Выполните запрос с использованием полученного id_sysDateLoad
            cur.execute(f'''
                INSERT INTO "orders" ("id_order", "id_sale", "id_customers", "id_restaurant", "id_employee", "cheque", "id_sysDateLoad", "sysDateLoad") 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (new_order_id, sale_id, customer_id, restaurant_id, employee_id, cheque, id_sys_date_load, sys_date_load))
            st.success("Order added successfully!")
        else:
            # Обработка случая, когда id_sysDateLoad не найден
            st.error(f"id_sysDateLoad for date {sys_date_load} not found")

# Add functionality to delete orders
st.sidebar.subheader("Delete Order")
order_to_delete = st.sidebar.text_input("Enter Order ID to delete:")
if st.sidebar.button("Delete Order"):
    try:
        cur.execute('DELETE FROM "orders" WHERE "id_order" = %s', (order_to_delete,))
        st.sidebar.success("Order deleted successfully!")
    except psycopg2.Error as e:
        st.sidebar.error(f"Error deleting order: {e}")

# Add table of employees and warehouse
cur.execute('SELECT * FROM "employee";')
employee_data = cur.fetchall()
df_employees = pd.DataFrame(employee_data, columns=[desc[0] for desc in cur.description])
st.sidebar.subheader("Employees Table:")
st.sidebar.write(df_employees)

cur.execute('SELECT * FROM "warehouse";')
warehouse_data = cur.fetchall()
df_warehouse = pd.DataFrame(warehouse_data, columns=[desc[0] for desc in cur.description])
st.sidebar.subheader("Warehouse Table:")
st.sidebar.write(df_warehouse)

# Commit the changes to the database.
conn.commit()

# Close the cursor and connection.
cur.close()
conn.close()
