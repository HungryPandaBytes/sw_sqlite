import pandas as pd
import sqlite3
import streamlit as st


# Define the URL of your Looker Studio report
report_url = "https://lookerstudio.google.com/embed/reporting/67160775-9563-45e9-a9e7-a01b3bb00868/page/p_f2mnuhz8pd"

# Create an iframe to embed the report
st.components.v1.html(
    f"""
    <iframe
        width="100%"
        height="500"
        src="{report_url}"
        frameborder="0"
        allowfullscreen
    ></iframe>
    """,
    height=600,
)

# Step 1: Load all Excel tabs to SQLite
def load_excel_to_sqlite(excel_path, db_path):
    # Create a connection to SQLite database
    conn = sqlite3.connect(db_path)
    
    # Get all sheet names
    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names
    
    # Dictionary to store column names for each sheet
    all_tables_info = {}
    
    # Process each sheet
    for sheet_name in sheet_names:
        # Read the sheet into a dataframe
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Create a valid table name from the sheet name
        # Replace spaces and special characters with underscores
        table_name = ''.join(c if c.isalnum() else '_' for c in sheet_name)
        
        # Write the data to a SQLite table
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Store column names for this sheet
        all_tables_info[table_name] = df.columns.tolist()
    
    # Close the connection
    conn.close()
    
    return all_tables_info, sheet_names

# Step 2: Connect Streamlit to SQLite
def create_streamlit_app(db_path, all_tables_info, sheet_names):
    st.title('Excel Data Explorer')
    
    # Create a connection to the database
    conn = sqlite3.connect(db_path)
    
    # Add a sheet/table selector
    original_sheet_name = st.selectbox('Select a sheet:', sheet_names)
    
    # Convert sheet name to table name (same conversion as in load function)
    table_name = ''.join(c if c.isalnum() else '_' for c in original_sheet_name)
    
    # Example query for the selected table
    query = f"SELECT * FROM '{table_name}' LIMIT 100"
    # query = "SELECT host_id, COUNT(vulnerability_id) AS vulnerability_count FROM cpe GROUP BY host_id;"

    df_sample = pd.read_sql_query(query, conn)
    
    # Display sheet information
    st.subheader(f'Data from sheet: {original_sheet_name}')
    st.write(f'Number of columns: {len(df_sample.columns)}')
    st.write(f'Number of rows in sample: {len(df_sample)}')

    # Display a sample of the data
    st.subheader('SeeWard Data')
    st.dataframe(df_sample)
    
    # Add basic statistics for numeric columns
    st.subheader('Basic Statistics (Numeric Columns)')
    numeric_df = df_sample.select_dtypes(include=['number'])
    if not numeric_df.empty:
        st.dataframe(numeric_df.describe())
    else:
        st.write("No numeric columns found in this sheet.")

    # Close the connection
    conn.close()

    
# Main execution
if __name__ == "__main__":
    excel_path = "Raw Seeward Data.xlsx"
    db_path = "seeward_data.db"
    
    # Load all Excel tabs to SQLite
    all_tables_info, sheet_names = load_excel_to_sqlite(excel_path, db_path)
    
    # Run Streamlit app
    create_streamlit_app(db_path, all_tables_info, sheet_names)