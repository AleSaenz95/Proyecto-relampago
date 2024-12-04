from flask import Flask, render_template, request
import pyodbc
import json  # Para serializar distribuciones correctamente

app = Flask(__name__)

DATABASE_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'tiusr3pl.cuc-carrera-ti.ac.cr',
    'database': 'tiusr3pl_Proyecto_Barba',
    'username': 'sitios',
    'password': 'SitiosC32024'
}

def get_db_connection():
    connection_string = (
        f"DRIVER={DATABASE_CONFIG['driver']};"
        f"SERVER={DATABASE_CONFIG['server']};"
        f"DATABASE={DATABASE_CONFIG['database']};"
        f"UID={DATABASE_CONFIG['username']};"
        f"PWD={DATABASE_CONFIG['password']};"
        f"Timeout=30;"
    )
    return pyodbc.connect(connection_string)

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener nombres de las columnas desde la base de datos
        cursor.execute("SELECT TOP 0 * FROM procedimientos")
        columnas = [desc[0] for desc in cursor.description]

        # Leer los valores de los filtros enviados por el usuario
        valores_filtro = {col: request.form.get(col, '') for col in columnas}

        # Generar valores únicos para cada columna (para los filtros)
        filtros = {}
        for columna in columnas:
            cursor.execute(f"SELECT DISTINCT RTRIM(LTRIM({columna})) AS {columna} FROM procedimientos")
            filtros[columna] = [row[0] for row in cursor.fetchall() if row[0] is not None]

        # Construir consulta dinámica con los filtros seleccionados
        query = f"SELECT {', '.join(columnas)} FROM procedimientos WHERE 1=1"
        params = []
        for col, valor in valores_filtro.items():
            if valor:
                query += f" AND {col} = ?"
                params.append(valor)

        # Ejecutar la consulta con los filtros
        cursor.execute(query, params)
        procedimientos = cursor.fetchall()

        # Recalcular distribuciones basadas en los datos filtrados
        distribuciones = {}
        for columna in columnas:
            cursor.execute(f"""
                SELECT RTRIM(LTRIM({columna})) AS valor, COUNT(*) AS cantidad
                FROM procedimientos
                WHERE 1=1 {''.join([f" AND {c} = ?" if valores_filtro[c] else '' for c in columnas])}
                GROUP BY {columna}
            """, params)
            resultados = cursor.fetchall()
            distribuciones[columna] = [{"valor": row[0], "cantidad": row[1]} for row in resultados if row[0] is not None]

        cursor.close()
        conn.close()

        # Serializamos distribuciones como JSON
        distribuciones_json = json.dumps(distribuciones)

        return render_template(
            'index.html',
            columnas=columnas,
            filtros=filtros,  # Incluimos los filtros
            procedimientos=procedimientos,
            valores_filtro=valores_filtro,
            distribuciones_json=distribuciones_json  # Pasamos distribuciones serializadas
        )
    except Exception as e:
        return f"Error al conectar con la base de datos: {e}"




if __name__ == '__main__':
    app.run(debug=True)
