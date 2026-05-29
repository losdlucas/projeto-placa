import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def verificar_placa(placa):

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM veiculos WHERE placa = %s",
        (placa,)
    )

    veiculo = cursor.fetchone()

    cursor.close()
    conn.close()

    return veiculo


def salvar_historico(placa, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO historico_placas (placa, status)
        VALUES (%s, %s)
        """,
        (placa, status)
    )

    conn.commit()

    cursor.close()
    conn.close()