import sqlite3

# Reemplaza con el nombre exacto de tu archivo de base de datos (.db)
conexion = sqlite3.connect("crioterapia.db") 
cursor = conexion.cursor()

# Modifica la tabla vieja agregando la columna que falta
cursor.execute("ALTER TABLE tratamientos ADD COLUMN temperatura_alerta TEXT;")

conexion.commit()
conexion.close()
print("¡Columna agregada exitosamente!")