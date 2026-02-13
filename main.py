import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# load csv file
print("Loading data")

df = pd.read_csv('can_data.csv')

print(f"\nDataset loaded successfully")
print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nColumn names:\n{df.columns.tolist()}")
print(f"\nFirst 5 rows:\n{df.head()}")
print(f"\nData info:")
print(df.info())
print(f"\nBasic statistics:\n{df.describe()}")

# cleaning data
print("\n" + "="*70)
print("Data Cleaning")

# removing dead sensors for cleaning
analog_columns = [col for col in df.columns if 'Analog Input' in col]
print(f"\nFound {len(analog_columns)} Analog Input columns")

dead_sensors = []
for col in analog_columns:
    unique_values = df[col].dropna().nunique()
    if unique_values <= 1:
        dead_sensors.append(col)
        print(f" Dead sensor detected: {col} (only {unique_values} unique value)")

print(f"\nRemoving {len(dead_sensors)} dead sensor column(s)...")
df_clean = df.drop(columns=dead_sensors)

# removing rows where data is missing
initial_row_count = len(df_clean)
df_clean = df_clean.dropna(subset=['RPM', 'TPS'])
rows_removed = initial_row_count - len(df_clean)
print(f"Removed {rows_removed} rows with missing RPM or TPS values")

# removing duplicate timestamps
duplicates = df_clean.duplicated(subset=['timestamp']).sum()
df_clean = df_clean.drop_duplicates(subset=['timestamp'])
print(f"Removed {duplicates} duplicate timestamp entries")

print(f"\nCleaned dataset shape: {df_clean.shape[0]} rows × {df_clean.shape[1]} columns")
print(f"Remaining Analog Input sensors: {[col for col in df_clean.columns if 'Analog Input' in col]}")

# finding insights
print("\n" + "="*70)
print("Insights")

# engine load percentage
df_clean['Engine_Load_Percent'] = (df_clean['TPS'] / df_clean['TPS'].max()) * 100

# categorizing RPM into operating ranges
df_clean['RPM_Category'] = pd.cut(
    df_clean['RPM'], 
    bins=[0, 1500, 2000, 2500, 3000, float('inf')],
    labels=['Idle (<1500)', 'Low (1500-2000)', 'Medium (2000-2500)', 
            'High (2500-3000)', 'Very High (>3000)']
)

# calculating fuel efficiency
df_clean['Fuel_Efficiency_Index'] = df_clean['Fuel Open Time'] / df_clean['RPM']

# printing insights
print("\nStatistical Summary:")
print(f"\nRPM (Revolutions Per Minute):")
print(f"  • Mean: {df_clean['RPM'].mean():.2f} RPM")
print(f"  • Median: {df_clean['RPM'].median():.2f} RPM")
print(f"  • Range: {df_clean['RPM'].min():.2f} - {df_clean['RPM'].max():.2f} RPM")
print(f"  • Standard Deviation: {df_clean['RPM'].std():.2f}")

print(f"\nTPS (Throttle Position Sensor):")
print(f"  • Mean: {df_clean['TPS'].mean():.2f}%")
print(f"  • Median: {df_clean['TPS'].median():.2f}%")
print(f"  • Range: {df_clean['TPS'].min():.2f}% - {df_clean['TPS'].max():.2f}%")

print(f"\nRPM Distribution by Category:")
category_counts = df_clean['RPM_Category'].value_counts().sort_index()
for category, count in category_counts.items():
    percentage = (count / len(df_clean)) * 100
    print(f"  • {category}: {count} records ({percentage:.1f}%)")

# analysis
print(f"\nCorrelation Analysis:")
print(f"  • RPM vs TPS: {df_clean['RPM'].corr(df_clean['TPS']):.3f}")
print(f"  • RPM vs Ignition Angle: {df_clean['RPM'].corr(df_clean['Ignition Angle']):.3f}")
if 'MAP' in df_clean.columns:
    map_corr = df_clean['RPM'].corr(df_clean['MAP'].dropna())
    print(f"  • RPM vs MAP: {map_corr:.3f}")

# graphing
print("\n" + "="*70)
print("Graphs and Visualizations")

# graph 1: line chart - RPM over time
print("\n1. Creating line chart: RPM over time...")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=df_clean['timestamp'],
    y=df_clean['RPM'],
    mode='lines',
    name='RPM',
    line=dict(color='#FF6B6B', width=1.5)
))
fig1.update_layout(
    title={
        'text': 'Engine RPM Over Time',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20}
    },
    xaxis_title='Timestamp (seconds)',
    yaxis_title='Engine RPM (Revolutions Per Minute)',
    template='plotly_white',
    hovermode='x unified',
    font=dict(size=12)
)
fig1.write_image('graph1_rpm_over_time.png', width=1200, height=600)
print("Saved: graph1_rpm_over_time.png")

# graph 2: scatter plot - RPM vs TPS
print("\n2. Creating scatter plot: RPM vs TPS...")
fig2 = px.scatter(
    df_clean,
    x='TPS',
    y='RPM',
    color='Engine_Load_Percent',
    title='Engine RPM vs Throttle Position',
    labels={
        'TPS': 'Throttle Position Sensor (%)',
        'RPM': 'Engine RPM',
        'Engine_Load_Percent': 'Engine Load (%)'
    },
    color_continuous_scale='Viridis'
)
fig2.update_layout(
    title={'x': 0.5, 'xanchor': 'center', 'font': {'size': 20}},
    template='plotly_white',
    font=dict(size=12)
)
fig2.write_image('graph2_rpm_vs_tps.png', width=1200, height=600)
print("Saved: graph2_rpm_vs_tps.png")

# graph 3: bar chart - average RPM by category
print("\n3. Creating bar chart: Average RPM by category...")
rpm_by_category = df_clean.groupby('RPM_Category', observed=True)['RPM'].mean().reset_index()
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=rpm_by_category['RPM_Category'],
    y=rpm_by_category['RPM'],
    marker_color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'],
    text=[f'{val:.0f}' for val in rpm_by_category['RPM']],
    textposition='outside'
))
fig3.update_layout(
    title={
        'text': 'Average Engine RPM by Operating Range',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20}
    },
    xaxis_title='RPM Category',
    yaxis_title='Average RPM',
    template='plotly_white',
    showlegend=False,
    font=dict(size=12)
)
fig3.write_image('graph3_rpm_by_category.png', width=1200, height=600)
print("Saved: graph3_rpm_by_category.png")

# graph 4: histogram - RPM distribution
print("\n4. Creating histogram: RPM distribution...")
fig4 = go.Figure()
fig4.add_trace(go.Histogram(
    x=df_clean['RPM'],
    nbinsx=50,
    marker_color='#4ECDC4',
    name='RPM'
))
fig4.update_layout(
    title={
        'text': 'Distribution of Engine RPM',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20}
    },
    xaxis_title='Engine RPM',
    yaxis_title='Frequency (Number of Occurrences)',
    template='plotly_white',
    showlegend=False,
    font=dict(size=12)
)
fig4.write_image('graph4_rpm_distribution.png', width=1200, height=600)
print("Saved: graph4_rpm_distribution.png")

# graph 5: multi-panel - RPM and TPS combined
print("\n5. Creating multi-panel chart: RPM and TPS over time...")
fig5 = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Engine RPM Over Time', 'Throttle Position (TPS) Over Time'),
    vertical_spacing=0.15
)

fig5.add_trace(go.Scatter(
    x=df_clean['timestamp'],
    y=df_clean['RPM'],
    mode='lines',
    name='RPM',
    line=dict(color='#FF6B6B', width=1.5)
), row=1, col=1)

fig5.add_trace(go.Scatter(
    x=df_clean['timestamp'],
    y=df_clean['TPS'],
    mode='lines',
    name='TPS',
    line=dict(color='#4ECDC4', width=1.5)
), row=2, col=1)

fig5.update_xaxes(title_text="Timestamp (seconds)", row=2, col=1)
fig5.update_yaxes(title_text="RPM", row=1, col=1)
fig5.update_yaxes(title_text="TPS (%)", row=2, col=1)

fig5.update_layout(
    title_text='Engine Performance Metrics Over Time',
    title_x=0.5,
    title_font_size=20,
    template='plotly_white',
    height=900,
    showlegend=True,
    font=dict(size=12)
)
fig5.write_image('graph5_combined_metrics.png', width=1200, height=900)
print("Saved: graph5_combined_metrics.png")

# summary of data
print("Analysis Completed")
print(f"\nKey Findings:")
print(f"  • Total records analyzed: {len(df_clean):,}")
print(f"  • Dead sensors removed: {len(dead_sensors)}")
print(f"  • Average RPM: {df_clean['RPM'].mean():.0f} RPM")
print(f"  • Most common operating range: {df_clean['RPM_Category'].mode()[0]}")
print(f"  • RPM-TPS correlation: {df_clean['RPM'].corr(df_clean['TPS']):.3f}")
