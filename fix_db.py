import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
try:
    cursor.execute("ALTER TABLE products ADD COLUMN description TEXT;")
    connection.commit()
    print("Column description added to products table.")
except Exception as e:
    print("Error:", e)
