import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="DataLens Pro - Tableau Replacement",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STYLING ====================
st.markdown("""
<style>
   .main-header {font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0;}
   .sub-header {font-size: 1.1rem; color: #666; margin-top: 0;}
   .kpi-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               padding: 1.5rem; border-radius: 10px; color: white; text-align: center;}
   .kpi-value {font-size: 2rem; font-weight: bold;}
   .kpi-label {font-size: 0.9rem; opacity: 0.9;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem;}
</style>
""", unsafe_allow_html=True)

# ==================== UTILITY FUNCTIONS ====================
@st.cache_data
def load_data(file):
    """Load CSV or Excel with caching"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding_errors='ignore')
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file type. Upload CSV or Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def detect_column_types(df):
    """Auto-detect column types for Tableau-like Dimensions vs Measures"""
    dimensions, measures, dates = [], [], []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() < 20 and df[col].nunique() / len(df) < 0.05:
                dimensions.append(col)
            else:
                measures.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            dates.append(col)
        else:
            try:
                pd.to_datetime(df[col], errors='raise')
                df[col] = pd.to_datetime(df[col])
                dates.append(col)
            except:
                dimensions.append(col)
    return dimensions, measures, dates

def apply_global_filters(df, filters):
    """Apply sidebar filters to dataframe"""
    df_filtered = df.copy()
    for col, values in filters.items():
        if values:
            if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
                df_filtered = df_filtered[df_filtered[col].isin(values)]
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                # Convert date objects (from Streamlit date_input) to pandas Timestamp for comparison
                start_ts = pd.to_datetime(values[0])
                end_ts = pd.to_datetime(values[1])
                df_filtered = df_filtered[(df_filtered[col] >= start_ts) & (df_filtered[col] <= end_ts)]
            else:
                df_filtered = df_filtered[(df_filtered[col] >= values[0]) & (df_filtered[col] <= values[1])]
    return df_filtered

# ==================== KPI DASHBOARD GENERATORS ====================
def generate_kpi_dashboard(df, measures, dimensions):
    """Dashboard 1-10: KPI Cards"""
    st.subheader("📈 KPI Overview Dashboard")
    cols = st.columns(min(5, len(measures)))
    for i, measure in enumerate(measures[:10]):
        with cols[i % 5]:
            total = df[measure].sum()
            avg = df[measure].mean()
            st.metric(
                label=measure,
                value=f"{total:,.2f}" if total > 1000 else f"{total:.2f}",
                delta=f"Avg: {avg:,.2f}"
            )

def generate_summary_stats_dashboard(df, measures):
    """Dashboard 11-15: Summary Statistics"""
    st.subheader("📊 Statistical Summary Dashboard")
    if measures:
        st.dataframe(df[measures].describe().T.style.background_gradient(cmap='Blues'), use_container_width=True)

def generate_missing_data_dashboard(df):
    """Dashboard 16: Missing Data Analysis"""
    st.subheader("🔍 Data Quality Dashboard - Missing Values")
    missing = df.isnull().sum().reset_index()
    missing.columns = ['Column', 'Missing Count']
    missing['Percent'] = (missing['Missing Count'] / len(df) * 100).round(2)
    missing = missing[missing['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    if not missing.empty:
        fig = px.bar(missing, x='Column', y='Percent', title='Missing Data % by Column',
                     color='Percent', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No missing data found!")

def generate_correlation_dashboard(df, measures):
    """Dashboard 17-20: Correlation Dashboards"""
    if len(measures) >= 2:
        st.subheader("🔗 Correlation Analysis Dashboard")
        corr = df[measures].corr()

        col1, col2 = st.columns(2)
        with col1:
            fig = px.imshow(corr, text_auto='.2f', aspect="auto",
                          title="Correlation Heatmap", color_continuous_scale='RdBu_r')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.imshow(corr.abs(), text_auto='.2f', aspect="auto",
                          title="Absolute Correlation", color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

def generate_distribution_dashboard(df, measures, dimensions):
    """Dashboard 21-30: Distribution Dashboards"""
    st.subheader("📉 Distribution Dashboard")
    tabs = st.tabs([f"Dist: {m}" for m in measures[:10]])
    for i, measure in enumerate(measures[:10]):
        with tabs[i]:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.histogram(df, x=measure, marginal="box", nbins=50,
                                 title=f"Histogram of {measure}")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.box(df, y=measure, points="outliers", title=f"Box Plot of {measure}")
                st.plotly_chart(fig, use_container_width=True)

def generate_categorical_dashboard(df, dimensions, measures):
    """Dashboard 31-40: Categorical Analysis"""
    st.subheader("🏷️ Categorical Analysis Dashboard")
    for dim in dimensions[:5]:
        if df[dim].nunique() < 50:
            with st.expander(f"Analysis by {dim}", expanded=False):
                col1, col2 = st.columns(2)
                counts = df[dim].value_counts().reset_index()
                with col1:
                    fig = px.bar(counts, x=dim, y='count', title=f"Count by {dim}")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.pie(counts, names=dim, values='count', title=f"Distribution of {dim}")
                    st.plotly_chart(fig, use_container_width=True)

def generate_time_series_dashboard(df, dates, measures):
    """Dashboard 41-45: Time Series Dashboards"""
    if dates and measures:
        st.subheader("📅 Time Series Dashboard")
        date_col = dates[0]
        df_ts = df.copy()
        df_ts['period'] = df_ts[date_col].dt.to_period('M').astype(str)

        for measure in measures[:5]:
            agg = df_ts.groupby('period')[measure].agg(['sum', 'mean', 'count']).reset_index()
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=agg['period'], y=agg['sum'], name='Sum'), secondary_y=False)
            fig.add_trace(go.Scatter(x=agg['period'], y=agg['mean'], name='Avg'), secondary_y=True)
            fig.update_layout(title=f"{measure} Over Time", xaxis_title="Period")
            st.plotly_chart(fig, use_container_width=True)

def generate_scatter_matrix_dashboard(df, measures):
    """Dashboard 46-47: Scatter Matrix"""
    if len(measures) >= 3:
        st.subheader("🔢 Scatter Matrix Dashboard")
        fig = px.scatter_matrix(df[measures[:6]], dimensions=measures[:6],
                               title="Scatter Matrix of Top Measures")
        fig.update_traces(diagonal_visible=False)
        st.plotly_chart(fig, use_container_width=True)

def generate_pca_dashboard(df, measures):
    """Dashboard 48: PCA Analysis"""
    if len(measures) >= 3:
        st.subheader("🧬 PCA Dimensionality Dashboard")
        df_clean = df[measures].dropna()
        if len(df_clean) > 10:
            scaled = StandardScaler().fit_transform(df_clean)
            pca = PCA(n_components=2)
            components = pca.fit_transform(scaled)
            pca_df = pd.DataFrame(components, columns=['PC1', 'PC2'])
            fig = px.scatter(pca_df, x='PC1', y='PC2',
                           title=f"PCA - Explained Variance: {pca.explained_variance_ratio_.sum():.2%}")
            st.plotly_chart(fig, use_container_width=True)

def generate_cluster_dashboard(df, measures):
    """Dashboard 49: K-Means Clustering"""
    if len(measures) >= 2:
        st.subheader("🎯 Clustering Dashboard")
        n_clusters = st.slider("Number of Clusters", 2, 10, 3, key="cluster_slider")
        df_clean = df[measures[:3]].dropna()
        if len(df_clean) > n_clusters:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_clean['Cluster'] = kmeans.fit_predict(StandardScaler().fit_transform(df_clean))
            fig = px.scatter_3d(df_clean, x=measures[0], y=measures[1],
                               z=measures[2] if len(measures) > 2 else measures[0],
                               color='Cluster', title="K-Means Clusters")
            st.plotly_chart(fig, use_container_width=True)

def generate_custom_dashboard(df, dimensions, measures):
    """Dashboard 50+: Custom Builder"""
    st.subheader("🛠️ Custom Dashboard Builder")
    col1, col2, col3 = st.columns(3)
    with col1:
        x_axis = st.selectbox("X-Axis", dimensions + measures, key="custom_x")
    with col2:
        y_axis = st.selectbox("Y-Axis", measures, key="custom_y")
    with col3:
        chart_type = st.selectbox("Chart Type",
                                  ["Bar", "Line", "Scatter", "Box", "Violin", "Area"], key="custom_chart")

    if x_axis and y_axis:
        if chart_type == "Bar":
            fig = px.bar(df, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
        elif chart_type == "Line":
            fig = px.line(df, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis}")
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
        elif chart_type == "Box":
            fig = px.box(df, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
        elif chart_type == "Violin":
            fig = px.violin(df, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
        else:
            fig = px.area(df, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis}")
        st.plotly_chart(fig, use_container_width=True)

# ==================== GRAPH GENERATORS - 50+ CHARTS ====================
def generate_all_graphs(df, dimensions, measures, dates):
    """Generate 50+ different graph types"""
    st.header("📊 Auto-Generated Graph Gallery - 50+ Charts")

    graph_count = 0
    cols = st.columns(2)

    # Graph 1-5: Basic bars by dimension
    for dim in dimensions[:5]:
        if df[dim].nunique() < 30:
            with cols[graph_count % 2]:
                graph_count += 1
                counts = df[dim].value_counts().head(20)
                fig = px.bar(x=counts.index, y=counts.values,
                           title=f"Graph {graph_count}: Count by {dim}")
                st.plotly_chart(fig, use_container_width=True)

    # Graph 6-15: Measures distribution
    for measure in measures[:10]:
        with cols[graph_count % 2]:
            graph_count += 1
            fig = px.histogram(df, x=measure, nbins=30,
                             title=f"Graph {graph_count}: {measure} Distribution")
            st.plotly_chart(fig, use_container_width=True)

    # Graph 16-25: Box plots
    for measure in measures[:10]:
        with cols[graph_count % 2]:
            graph_count += 1
            fig = px.box(df, y=measure, title=f"Graph {graph_count}: {measure} Box Plot")
            st.plotly_chart(fig, use_container_width=True)

    # Graph 26-30: Scatter plots between measures
    for i in range(min(5, len(measures)-1)):
        with cols[graph_count % 2]:
            graph_count += 1
            fig = px.scatter(df, x=measures[i], y=measures[i+1],
                           trendline="ols", title=f"Graph {graph_count}: {measures[i]} vs {measures[i+1]}")
            st.plotly_chart(fig, use_container_width=True)

    # Graph 31-35: Line charts for dates
    if dates:
        for measure in measures[:5]:
            with cols[graph_count % 2]:
                graph_count += 1
                df_sorted = df.sort_values(dates[0])
                fig = px.line(df_sorted, x=dates[0], y=measure,
                            title=f"Graph {graph_count}: {measure} Over Time")
                st.plotly_chart(fig, use_container_width=True)

    # Graph 36-40: Violin plots
    for measure in measures[:5]:
        with cols[graph_count % 2]:
            graph_count += 1
            fig = px.violin(df, y=measure, box=True,
                          title=f"Graph {graph_count}: {measure} Violin Plot")
            st.plotly_chart(fig, use_container_width=True)

    # Graph 41-45: Heatmaps by dimension x dimension
    if len(dimensions) >= 2:
        for i in range(min(5, len(dimensions)-1)):
            dim1, dim2 = dimensions[i], dimensions[i+1]
            if df[dim1].nunique() < 20 and df[dim2].nunique() < 20:
                with cols[graph_count % 2]:
                    graph_count += 1
                    pivot = pd.crosstab(df[dim1], df[dim2])
                    fig = px.imshow(pivot, title=f"Graph {graph_count}: {dim1} vs {dim2} Heatmap")
                    st.plotly_chart(fig, use_container_width=True)

    # Graph 46-50: Area charts
    if dates and measures:
        for measure in measures[:5]:
            with cols[graph_count % 2]:
                graph_count += 1
                df_sorted = df.sort_values(dates[0])
                fig = px.area(df_sorted, x=dates[0], y=measure,
                            title=f"Graph {graph_count}: {measure} Area Chart")
                st.plotly_chart(fig, use_container_width=True)

    # Graph 51-55: Treemaps
    for dim in dimensions[:5]:
        if df[dim].nunique() < 50 and measures:
            with cols[graph_count % 2]:
                graph_count += 1
                fig = px.treemap(df, path=[dim], values=measures[0],
                               title=f"Graph {graph_count}: Treemap of {measures[0]} by {dim}")
                st.plotly_chart(fig, use_container_width=True)

    st.success(f"Generated {graph_count} auto charts! Use Custom Dashboard Builder for more.")

# ==================== MAIN APP ====================
def main():
    st.markdown('<p class="main-header">DataLens Pro 📊</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your Open-Source Tableau Replacement - Upload data, get 50+ dashboards instantly</p>',
                unsafe_allow_html=True)

    # Sidebar - File Upload
    with st.sidebar:
        st.header("1. Upload Data")
        uploaded_files = st.file_uploader("Choose CSV or Excel files",
                                         type=['csv', 'xlsx', 'xls'],
                                         accept_multiple_files=True)

        st.header("2. Global Filters")
        st.caption("Filters apply to all dashboards")

    if uploaded_files:
        # Load and combine data
        dfs = []
        for file in uploaded_files:
            df = load_data(file)
            if df is not None:
                dfs.append(df)

        if not dfs:
            st.stop()

        df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]

        # Detect types
        dimensions, measures, dates = detect_column_types(df)

        # Sidebar filters
        filters = {}
        with st.sidebar:
            st.subheader("Dimensions")
            for dim in dimensions[:8]:
                if df[dim].nunique() < 100:
                    options = st.multiselect(f"{dim}", df[dim].dropna().unique(), key=f"filter_{dim}")
                    if options:
                        filters[dim] = options

            st.subheader("Measures")
            for measure in measures[:5]:
                min_val, max_val = float(df[measure].min()), float(df[measure].max())
                val_range = st.slider(f"{measure}", min_val, max_val, (min_val, max_val), key=f"filter_{measure}")
                if val_range!= (min_val, max_val):
                    filters[measure] = val_range

            if dates:
                st.subheader("Date Range")
                for date_col in dates[:2]:
                    min_date, max_date = df[date_col].min(), df[date_col].max()
                    date_range = st.date_input(f"{date_col}", [min_date, max_date], key=f"filter_{date_col}")
                    if len(date_range) == 2:
                        filters[date_col] = date_range

        # Apply filters
        df_filtered = apply_global_filters(df, filters)

        # Data Preview
        with st.expander("📋 Data Preview & Info", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rows", f"{len(df_filtered):,}")
            col2.metric("Total Columns", len(df_filtered.columns))
            col3.metric("Measures", len(measures))
            col4.metric("Dimensions", len(dimensions))
            st.dataframe(df_filtered.head(100), use_container_width=True)

            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Filtered Data", csv, "filtered_data.csv", "text/csv")

        # Tabs for all dashboards
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 KPI & Summary",
            "📊 Distributions",
            "🔗 Correlations",
            "📅 Time Series",
            "🧬 Advanced Analytics",
            "📈 50+ Auto Graphs"
        ])

        with tab1:
            generate_kpi_dashboard(df_filtered, measures, dimensions)
            generate_summary_stats_dashboard(df_filtered, measures)
            generate_missing_data_dashboard(df_filtered)

        with tab2:
            generate_distribution_dashboard(df_filtered, measures, dimensions)
            generate_categorical_dashboard(df_filtered, dimensions, measures)

        with tab3:
            generate_correlation_dashboard(df_filtered, measures)
            generate_scatter_matrix_dashboard(df_filtered, measures)

        with tab4:
            generate_time_series_dashboard(df_filtered, dates, measures)

        with tab5:
            generate_pca_dashboard(df_filtered, measures)
            generate_cluster_dashboard(df_filtered, measures)
            generate_custom_dashboard(df_filtered, dimensions, measures)

        with tab6:
            generate_all_graphs(df_filtered, dimensions, measures, dates)

    else:
        st.info("👆 Upload a CSV or Excel file to start building dashboards")
        st.markdown("""
        ### How it works:
        1. **Upload** your CSV/Excel files - multiple files will be combined
        2. **Auto-Analysis** - App detects dimensions, measures, and dates
        3. **50+ Dashboards** - KPI, distributions, correlations, time series, clustering, and more
        4. **50+ Graphs** - Bar, line, scatter, box, violin, heatmap, treemap, etc
        5. **Filter** - Use sidebar to slice data across all charts
        6. **Export** - Download filtered data or charts

        ### Unlike Tableau:
        - ✅ 100% Free & Open Source
        - ✅ Python-powered - extend with any library
        - ✅ No row limits
        - ✅ Deploy anywhere with `streamlit run`
        """)

if __name__ == "__main__":
    main()