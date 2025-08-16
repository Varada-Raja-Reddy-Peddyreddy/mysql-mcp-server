import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env variables if present
load_dotenv()

mcp = FastMCP(name="mysql_mcp_server")

def get_db_connection():
    """Create and return a new MySQL connection using env vars"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
            port=int(os.getenv("DB_PORT", 3306)),
        )
        return conn
    except Error as e:
        return None

@mcp.tool()
def list_tables() -> str:
    """Returns the list of tables in the database"""
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to the database."
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        if not tables:
            return "(no tables found)"
        return "\n".join(table[0] for table in tables)
    except Error as e:
        return f"Error executing SHOW TABLES: {str(e)}"
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Returns the schema (DESCRIBE) of the specified table"""
    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to the database."
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`;")
        description = cursor.fetchall()
        if not description:
            return f"No description found for table '{table_name}'."

        # Format output similar to SHOW COLUMNS
        lines = []
        header = ["Field", "Type", "Null", "Key", "Default", "Extra"]
        lines.append(" | ".join(header))
        for row in description:
            # Each row: (Field, Type, Null, Key, Default, Extra)
            lines.append(" | ".join(str(col) if col is not None else "NULL" for col in row))
        return "\n".join(lines)
    except Error as e:
        return f"Error executing DESCRIBE: {str(e)}"
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def read_only_query(query: str) -> str:
    """
    Runs a read-only SELECT query safely.
    Only SELECT queries are allowed for safety.
    """
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."

    conn = get_db_connection()
    if not conn:
        return "Error: Could not connect to the database."
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = cursor.column_names
        if not rows:
            return "(no rows returned)"
        
        # Format output as a simple table string
        header = " | ".join(columns)
        lines = [header]
        for row in rows:
            lines.append(" | ".join(str(cell) if cell is not None else "NULL" for cell in row))
        return "\n".join(lines)
    except Error as e:
        return f"Error executing query: {str(e)}"
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Starting MySQL MCP server...")
    mcp.run(transport="stdio")
