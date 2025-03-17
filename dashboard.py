import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt


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

# Load Data
@st.cache_data
def load_data():
    file_path = "Raw Seeward Data.xlsx"  # Replace with your file path
    try:
        cpe_data = pd.read_excel(file_path, sheet_name="cpe")
        host_data = pd.read_excel(file_path, sheet_name="host")
        vulnerability_data = pd.read_excel(file_path, sheet_name="cve")
        return cpe_data, host_data, vulnerability_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

cpe_data, host_data, vulnerability_data = load_data()

if cpe_data is None or host_data is None or vulnerability_data is None:
    st.stop()

# Dashboard Title
st.title("Cybersecurity Dashboard")

# Sidebar for View Selection
view = st.sidebar.selectbox("Select Dashboard View", ["IT Manager", "CISO"])

# IT Manager Dashboard
if view == "IT Manager":
    st.header("IT Manager Dashboard")
    
    # Tabs for IT Manager Dashboard Sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Vulnerabilities", "Critical Assets", "Remediation", "Resource Allocation"])

    with tab1:
        st.subheader("Overview")
        total_assets = host_data['id'].nunique()
        asset_types = host_data.groupby('type')['id'].nunique()
        st.write('host_data',host_data)

        st.metric("Total Assets", total_assets)
        st.bar_chart(asset_types)

        # Example DataFrame for stacked bar chart
        df = pd.DataFrame({
            'Type': ['Type A', 'Type B', 'Type C'],
            'High Sensitivity': [10, 15, 5],
            'Low Sensitivity': [20, 10, 25]
        })

        df = df.melt('Type', var_name='Sensitivity', value_name='Count')

        chart = alt.Chart(df).mark_bar().encode(
            x='Type',
            y='Count',
            color='Sensitivity'
        ).properties(title="Asset Types By Sensitivity")

        st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.subheader("Vulnerabilities")
        vulnerable_assets = cpe_data.merge(vulnerability_data, left_on='vulnerability_id', right_on='id')
        vulnerable_count = vulnerable_assets['host_id'].nunique()
        percentage_vulnerable = (vulnerable_count / total_assets) * 100
        
        st.metric("Percentage of Vulnerable Assets", f"{percentage_vulnerable:.2f}%")
        
        aging_bins = [0, 30, 60, 90, float('inf')]
        aging_labels = ['<30 days', '30-60 days', '60-90 days', '>90 days']
        vulnerability_data['aging_category'] = pd.cut(
            (pd.to_datetime(vulnerability_data['last_modified_date']) - pd.to_datetime(vulnerability_data['published_date'])).dt.days,
            bins=aging_bins,
            labels=aging_labels
        )
        
        aging_counts = vulnerability_data.groupby('aging_category')['id'].count()
        st.bar_chart(aging_counts)

    with tab3:
        st.subheader("Critical Assets at Risk")
        critical_assets = host_data[host_data['criticality'] == 'critical']
        critical_vulnerabilities = critical_assets.merge(vulnerable_assets, left_on='id', right_on='host_id')
        
        if not critical_vulnerabilities.empty:
            st.dataframe(critical_vulnerabilities[['hostname', 'ip', 'criticality']])
        else:
            st.write("No critical assets with vulnerabilities found.")

    with tab4:
        st.subheader("Remediation Progress")
        
        remediated_vulns = vulnerability_data[vulnerability_data['severity'] == 'remediated']
        total_vulns = vulnerability_data['id'].count()
        remediation_percentage = (remediated_vulns.shape[0] / total_vulns) * 100
        
        st.metric("Vulnerabilities Remediated", f"{remediation_percentage:.2f}%")
        
        avg_mttr = vulnerability_data.groupby('severity').apply(
            lambda x: (pd.to_datetime(x['last_modified_date']) - pd.to_datetime(x['published_date'])).dt.days.mean()
        )
        
        if not avg_mttr.empty:
            st.line_chart(avg_mttr)
    
    with tab5:
        st.subheader("Resource Allocation")
        
        if 'asset_team' in cpe_data.columns:
            team_workload = cpe_data.groupby('asset_team')['vulnerability_id'].count()
            unassigned_vulns = cpe_data[cpe_data['asset_team'].isnull()]['vulnerability_id'].count()
            
            st.bar_chart(team_workload)
            st.metric("Unassigned Vulnerabilities", unassigned_vulns)

# CISO Dashboard
elif view == "CISO":
    st.header("CISO Dashboard")

    # Tabs for CISO Dashboard Sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Executive Summary", "Vulnerability Breakdown", "Assets Breakdown",
        "Remediation Progress", "Threat Context", "Subsidiary Insights",
        "Drill-Down Capabilities", "Key Performance Indicators"
    ])

    with tab1:
        st.subheader("Executive Summary")
        
        overall_risk_score = vulnerability_data['cvss3_score'].mean()
        
        risk_trend_30_days = vulnerability_data[vulnerability_data['published_date'] >= '2025-01-29']['cvss3_score'].mean()
        
        total_vulnerabilities = vulnerability_data.shape[0]
        
        critical_assets_with_vulns = host_data[host_data['criticality'] == 'critical']['id'].nunique()
        
        col1, col2 = st.columns(2)
        
        col1.metric("Overall Risk Score", f"{overall_risk_score:.2f}")
        
        col2.metric("Risk Trend (Last 30 Days)", f"{risk_trend_30_days:.2f}")
        
        col1.metric("Total Vulnerabilities", total_vulnerabilities)
        
        col2.metric("Critical Assets with Vulnerabilities", critical_assets_with_vulns)

    with tab2:
        st.subheader("Vulnerability Breakdown")
        
        severity_breakdown = vulnerability_data.groupby('severity')['id'].count()
        
        top_10_critical_vulns = vulnerability_data[vulnerability_data['severity'] == 'critical'].nlargest(10, 'cvss3_score')
        
        asset_type_breakdown = cpe_data.merge(host_data[['id', 'type']], left_on='host_id', right_on='id').groupby('type')['vulnerability_id'].count()
        
        col1, col2 = st.columns(2)
        
        col1.bar_chart(severity_breakdown)
        
        col2.bar_chart(asset_type_breakdown)
        
    # Add other tabs similarly based on the requirements...
