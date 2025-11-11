import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Daily Sales Dashboard", layout="wide")
st.title("📊 Daily Sales Dashboard")

# --------------------------
# 📁 Upload Excel File
# --------------------------
uploaded_file = st.file_uploader("Upload your Excel file (xlsx)", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='sales', engine='openpyxl')

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Year'] = df['Date'].dt.year
        else:
            st.error("❌ 'Date' column not found in the uploaded file.")
            st.stop()

        # --------------------------
        # 🌐 Sidebar Filters
        # --------------------------
        st.sidebar.header("🔍 Filters")

        years = ["All"] + sorted(df['Year'].dropna().unique().tolist())
        branches = ["All"] + sorted(df['الفرع'].dropna().astype(str).unique().tolist()) if 'الفرع' in df.columns else ["All"]
        categories = ["All"] + sorted(df['Category'].dropna().astype(str).unique().tolist()) if 'Category' in df.columns else ["All"]

        selected_year = st.sidebar.selectbox("Select Year:", years, index=0)
        selected_branch = st.sidebar.selectbox("Select Branch:", branches, index=0)
        selected_category = st.sidebar.selectbox("Select Category:", categories, index=0)

        # Apply filters
        filtered_df = df.copy()
        if selected_year != "All":
            filtered_df = filtered_df[filtered_df['Year'] == selected_year]
        if selected_branch != "All" and 'الفرع' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['الفرع'].astype(str) == selected_branch]
        if selected_category != "All" and 'Category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Category'].astype(str) == selected_category]

        st.write(f"### Filtered Data: {filtered_df.shape[0]:,} rows")

        # --------------------------
        # 🧭 Key Metrics
        # --------------------------
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)

        if 'sales' in filtered_df.columns:
            total_sales = filtered_df['sales'].sum()
            avg_sales = filtered_df['sales'].mean()
            col1.metric("Total Sales", f"{total_sales:,.2f}")
            col2.metric("Average Sales", f"{avg_sales:,.2f}")
        else:
            col1.metric("Total Sales", "N/A")
            col2.metric("Average Sales", "N/A")

        if 'Order Ref' in filtered_df.columns:
            num_transactions = filtered_df['Order Ref'].nunique()
        else:
            num_transactions = filtered_df.shape[0]
        col3.metric("Total Transactions", f"{num_transactions:,}")

        # --------------------------
        # 📅 Yearly Comparison
        # --------------------------
        if 'Year' in filtered_df.columns and 'sales' in filtered_df.columns:
            year_sales = filtered_df.groupby('Year')['sales'].sum().reset_index()

            if 'Order Ref' in filtered_df.columns:
                year_trans = filtered_df.groupby('Year')['Order Ref'].nunique().reset_index()
                year_trans.rename(columns={'Order Ref': 'Transactions'}, inplace=True)
            else:
                year_trans = filtered_df.groupby('Year').size().reset_index(name='Transactions')

            yearly_summary = pd.merge(year_sales, year_trans, on='Year', how='outer')

            st.subheader("📆 Yearly Performance")

            coly1, coly2 = st.columns(2)
            for year_col, col in zip([2024, 2025], [coly1, coly2]):
                if year_col in yearly_summary['Year'].values:
                    sales_val = yearly_summary.loc[yearly_summary['Year']==year_col, 'sales'].values[0]
                    trans_val = yearly_summary.loc[yearly_summary['Year']==year_col, 'Transactions'].values[0]
                    col.metric(f"Total Sales ({year_col})", f"{sales_val:,.2f}")
                    col.metric(f"Transactions ({year_col})", f"{trans_val:,}")
                else:
                    col.metric(f"Total Sales ({year_col})", "No data")
                    col.metric(f"Transactions ({year_col})", "No data")

            # Charts
            st.subheader("💰 Sales by Year")
            fig_year = px.bar(
                yearly_summary,
                x='Year',
                y='sales',
                text='sales',
                title="Total Sales by Year",
                color='Year'
            )
            fig_year.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_year, use_container_width=True)

            st.subheader("🧾 Transactions by Year")
            fig_trans = px.bar(
                yearly_summary,
                x='Year',
                y='Transactions',
                text='Transactions',
                title="Number of Transactions by Year",
                color='Year'
            )
            fig_trans.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_trans, use_container_width=True)

        # --------------------------
        # 📈 Sales Trend (1–9 Nov 2025)
        # --------------------------
        st.subheader("📈 Sales Trend Over Time (1–9 Nov 2025)")

        mask = (filtered_df['Date'] >= '2025-11-01') & (filtered_df['Date'] <= '2025-11-09')
        nov_2025_df = filtered_df.loc[mask].copy()

        if not nov_2025_df.empty:
            nov_2025_df['Date_only'] = nov_2025_df['Date'].dt.date
            sales_time = nov_2025_df.groupby('Date_only')['sales'].sum().reset_index()

            fig1 = px.line(
                sales_time,
                x='Date_only',
                y='sales',
                title="Sales Trend: 1–9 November 2025",
                markers=True
            )
            fig1.update_layout(
                yaxis_title='Sales',
                xaxis_title='Date',
                xaxis=dict(tickformat="%d-%b"),
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("⚠️ No data found between 1–9 November 2025.")

        # --------------------------
        # 🏷️ Top Categories
        # --------------------------
        if 'Category' in filtered_df.columns:
            top_cat = filtered_df.groupby('Category')['sales'].sum().sort_values(ascending=False).reset_index()
            st.subheader("🏷️ Top Categories by Sales")
            fig2 = px.bar(top_cat, x='Category', y='sales', title="Top Categories")
            st.plotly_chart(fig2)

        # --------------------------
        # 🛒 Top Products
        # --------------------------
        if 'Order Lines/Product' in filtered_df.columns:
            top_prod = (
                filtered_df.groupby('Order Lines/Product')['sales']
                .sum()
                .sort_values(ascending=False)
                .reset_index()
                .head(10)
            )
            st.subheader("🛒 Top 10 Products by Sales")
            fig3 = px.bar(top_prod, x='Order Lines/Product', y='sales', title="Top 10 Products")
            st.plotly_chart(fig3)

        # --------------------------
        # 🏢 Sales by Branch
        # --------------------------
        if 'الفرع' in filtered_df.columns:
            sales_branch = filtered_df.groupby(filtered_df['الفرع'].astype(str))['sales'].sum().sort_values(ascending=False).reset_index()
            sales_branch.rename(columns={'الفرع': 'Branch'}, inplace=True)
            st.subheader("🏢 Sales by Branch")
            fig4 = px.pie(sales_branch, names='Branch', values='sales', title="Sales Distribution by Branch")
            st.plotly_chart(fig4)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("📂 Please upload your Excel file to display the dashboard.")
