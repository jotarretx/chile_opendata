import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Visualizador de Cambio de Precio por Producto") # Título en español

# 1. Carga de Datos (desde el archivo ya agrupado)
file_path = 'processed/grouped_precios.parquet' # Load from the already grouped file
try:
    df_grouped = pd.read_parquet(file_path)
    st.success(f"Datos agrupados cargados exitosamente desde {file_path}") # Mensaje de éxito en español

    # Ensure 'mes' and 'anyo' are suitable for creating a time index
    # Convert 'mes' and 'anyo' to string and pad 'mes' with leading zero if necessary
    df_grouped['mes_str'] = df_grouped['mes'].astype(str).str.zfill(2)
    df_grouped['anyo_str'] = df_grouped['anyo'].astype(str)

    # Create a combined time column for chronological plotting
    df_grouped['anyo_mes'] = df_grouped['anyo_str'] + '-' + df_grouped['mes_str']

    # Convert 'anyo_mes' to datetime for proper sorting and plotting on time axis
    try:
        df_grouped['anyo_mes'] = pd.to_datetime(df_grouped['anyo_mes'], format='%Y-%m')
    except Exception as dt_error:
        st.warning(f"No se pudo convertir 'anyo_mes' a formato de fecha. La gráfica podría no ordenarse cronológicamente. Error: {dt_error}")
        # If conversion fails, keep it as string for plotting, but warn the user
        df_grouped['anyo_mes'] = df_grouped['anyo_str'] + '-' + df_grouped['mes_str']

    # Ensure data is sorted by the time column for correct line plotting
    df_grouped = df_grouped.sort_values(by='anyo_mes')


except FileNotFoundError:
    st.error(f"Error: No se encontró el archivo {file_path}. Por favor, verifica la ruta.") # Mensaje de error en español
    st.stop() # Detener ejecución si los datos no se cargan
except Exception as e:
    st.error(f"Error al cargar o procesar los datos: {e}")
    st.stop()


st.sidebar.header("Configuración de Visualización") # Encabezado de la barra lateral en español

# 2. Selección de Productos para Visualizar
#    Obtener la lista única de productos desde el DataFrame agrupado
productos_disponibles = df_grouped['producto'].unique().tolist()
# Set 'Palta' as the default selected product
default_selection = ['Palta'] if 'Palta' in productos_disponibles else []
if not default_selection and productos_disponibles:
    default_selection = [productos_disponibles[0]] # Fallback to the first product if Palta not found

selected_productos = st.sidebar.multiselect(
    "Selecciona Productos para Visualizar", # Etiqueta en español
    productos_disponibles,
    default=default_selection # Set default selection
)

# 3. Filtrar el DataFrame agrupado basado en la selección de productos
filtered_df_grouped = pd.DataFrame()
df_agg_for_plot = pd.DataFrame()

if selected_productos:
    # Filter the grouped DataFrame based on selected products
    filtered_df_grouped = df_grouped[df_grouped['producto'].isin(selected_productos)].copy()

    # --- Second Aggregation Step for Plotting ---
    # Group by product and the combined time column (again), and calculate the mean price
    # This handles cases where 'unidad' might cause multiple entries per month/year
    df_agg_for_plot = filtered_df_grouped.groupby(['producto', 'anyo_mes'])['precio_promedio'].mean().reset_index()

    # Ensure the data for plotting is sorted by time
    df_agg_for_plot = df_agg_for_plot.sort_values(by='anyo_mes')
    # ---------------------------------------------

    # Debugging: Show the aggregated data used for plotting
    st.sidebar.header("Opciones de Depuración")
    if st.sidebar.checkbox("Mostrar datos agregados para gráfico"):
        st.subheader("Datos Agregados para Gráfico (df_agg_for_plot)")
        if not df_agg_for_plot.empty:
            st.dataframe(df_agg_for_plot)
        else:
            st.info("El DataFrame agregado para el gráfico está vacío.")


else:
    st.warning("Por favor, selecciona al menos un producto para visualizar.") # Mensaje de advertencia en español


# 4. Generar Visualización usando Plotly Express (Estática con Datos Agregados para Gráfico)
st.header("Evolución del Precio Promedio por Producto (Mensual)") # Encabezado en español

# Use df_agg_for_plot for plotting
if not df_agg_for_plot.empty:
    try:
        # Create the static line plot using the aggregated data for plotting
        fig = px.line(
            df_agg_for_plot, # Use the data aggregated specifically for plotting
            x='anyo_mes', # Use the datetime column for the x-axis for proper time scale
            y='precio_promedio',
            color='producto', # Use 'producto' to create separate lines for each product
            title="Evolución del Precio Promedio por Mes y Año", # Título del gráfico en español
            labels={ # Etiquetas de ejes en español
                'anyo_mes': 'Fecha (Año-Mes)',
                'precio_promedio': 'Precio Promedio',
                'producto': 'Producto'
            },
            hover_data={ # Mostrar información adicional al pasar el ratón
                'anyo_mes': '|%Y-%m', # Format date nicely
                'precio_promedio': ':.2f', # Format price
                'producto': True,
                # 'unidad': True, # Unidad is not in df_agg_for_plot
                # 'mes': False,
                # 'anyo': False
            }
            # Removed animation_frame parameter
            # Removed range_y for now, Plotly will auto-adjust
        )

        # Update layout for better appearance (optional)
        fig.update_layout(
            xaxis_title="Fecha (Año-Mes)", # Título del eje X
            yaxis_title="Precio Promedio", # Título del eje Y
            legend_title="Producto", # Título de la leyenda
            hovermode='x unified' # Improve hover behavior
        )

        # Display the static plot in Streamlit
        st.plotly_chart(fig, use_container_width=True) # use_container_width makes the plot responsive

    except Exception as e:
        st.error(f"Error generando el gráfico: {e}") # Mensaje de error en español

else:
    if selected_productos: # Only show this warning if products were selected but df_agg_for_plot is empty
         st.warning("No hay datos disponibles para los productos seleccionados después de la agregación para el gráfico.")
    else:
        st.warning("Por favor, selecciona al menos un producto para visualizar.")


# 5. Opcional: Mostrar información/muestra de datos (en la barra lateral)
# Note: This section now refers to the data loaded from grouped_precios.parquet
st.sidebar.header("Información de Datos Cargados (desde grouped_precios.parquet)") # Nuevo encabezado en la barra lateral
if st.sidebar.checkbox("Mostrar información/muestra"): # Checkbox en español
    st.subheader("Información de Datos Cargados (desde grouped_precios.parquet)") # Subencabezado en español

    if not df_grouped.empty:
        # Opción para mostrar describe()
        if st.checkbox("Mostrar .describe()"): # Etiqueta en español
            st.write("Estadísticas Descriptivas:") # Título en español
            st.write(df_grouped.describe())

        # Opción para mostrar un sample()
        if st.checkbox("Mostrar una muestra (.sample())"): # Etiqueta en español
            sample_size = st.number_input(
                "Número de filas para la muestra", # Etiqueta en español
                min_value=1,
                max_value=len(df_grouped), # El máximo es el tamaño del DataFrame cargado
                value=min(10, len(df_grouped)), # Valor por defecto: 10 o el tamaño total si es menor
                key="sample_size_input_grouped" # Added a unique key
            )
            st.write(f"Muestra aleatoria de {sample_size} filas:") # Título en español
            actual_sample_size = min(sample_size, len(df_grouped))
            st.dataframe(df_grouped.sample(n=actual_sample_size, random_state=42)) # Added random_state for reproducibility

        # Opcional: Mostrar el conteo de nulos para los datos cargados
        if st.checkbox("Mostrar conteo de nulos (Datos Cargados)"): # Etiqueta en español
             st.write("Conteo de Nulos por Columna (Datos Cargados):") # Título en español
             null_counts_grouped = df_grouped.isnull().sum()
             st.dataframe(null_counts_grouped)

    else:
        st.warning("No hay datos cargados para mostrar información.") # Mensaje de advertencia en español

# Removed the original data info section as we are now loading from the grouped file
# If you still need info on the *very* original data before your grouping,
# you would need to load that file separately or include that info elsewhere.