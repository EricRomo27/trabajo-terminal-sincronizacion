import pandas as pd
import sqlite3

# --- Configuración ---
archivo_csv = 'TT1.csv'
nombre_db = 'contaminantes.db'
nombre_tabla = 'calidad_aire'

print(f"Iniciando la carga de datos desde '{archivo_csv}'...")

# 1. Leer los datos del CSV
df = pd.read_csv(archivo_csv)

# 2. **Limpieza de Nombres de Columnas**
#    Elimina los espacios en blanco al inicio y final de los nombres
df.columns = df.columns.str.strip()
print("Nombres de columnas limpiados:", df.columns.tolist())


# 3. **Conversión de la Columna de Fecha**
#    Convierte la columna 'Fecha' de texto a un formato de fecha (datetime)
df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
print("La columna 'Fecha' ha sido convertida a formato de fecha.")

# 4. **Conexión a la Base de Datos SQLite**
#    Si el archivo .db no existe, Python lo creará automáticamente.
conn = sqlite3.connect(nombre_db)
print(f"Conectado a la base de datos '{nombre_db}'.")

# 5. **Guardar los Datos en la Tabla**
#    'if_exists='replace'' asegura que si ejecutas el script de nuevo,
#    la tabla se borrará y se volverá a crear con los datos limpios.
df.to_sql(nombre_tabla, conn, if_exists='replace', index=False)
print(f"Los datos han sido guardados exitosamente en la tabla '{nombre_tabla}'.")

# 6. **Verificación (Opcional)**
#    Leemos los primeros 5 registros de la tabla recién creada para confirmar
print("\nVerificación: Primeras 5 filas de la tabla en la base de datos:")
df_verificacion = pd.read_sql_query(f"SELECT * FROM {nombre_tabla} LIMIT 5", conn)
print(df_verificacion)


# 7. **Cerrar la Conexión**
conn.close()
print("\nProceso completado. La conexión a la base de datos ha sido cerrada.")