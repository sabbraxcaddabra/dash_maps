import dash
from dash import dcc, html, Output, Input, State
import dash_bootstrap_components as dbc
import os
import pandas as pd
import json

import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import arrow_function, assign

HERE = os.path.dirname(__file__)
REGIONS_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, ".", "regi.csv")))
CITIES_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, ".", "cities.csv")))

reg_df = pd.read_csv(REGIONS_FILE)
city_df = pd.read_csv(CITIES_FILE)

def set_regio_color_properties(geo_data: dict):
    dict_reg_df = reg_df.to_dict('records')
    for reg in dict_reg_df:
        try:
            true_feature = list(filter(lambda x: reg['Код региона'] == x['properties']['id'], geo_data['features']))[0]
        except IndexError:
            continue
        true_feature['properties']['enrolled'] = reg['Поступило']
        true_feature['properties']['celo'] = reg['Очное - Целевая квота']
        true_feature['properties']['name_ru'] = reg['Название региона']

    return geo_data

def get_enrolled_info_on_hover(feature=None):
    header = [html.H4('Распеделение кол-ва зачисленных по регионам РФ')]
    if not feature:
        return header + [html.P("Наведите на регион")]
    enrolled = feature['properties']['enrolled']
    reg_name = feature['properties']['name_ru']

    return header + [html.B(reg_name), html.Br(),
                     f'{enrolled} человек',
                     html.Br(),
                     'Для отображения развернутой статистики нажмите на контур региона'
                     ]


with open('geodata/russia_2021.geojson', 'r', encoding='utf-8') as file:
    GEO_DATA = json.load(file)
    GEO_DATA = set_regio_color_properties(GEO_DATA)

def generate_region_total_layout_enrolled(region_dict: dict):
    '''
    Генерация таблицы с общей статистикой
    :param region_dict: Словарь с общей статистикой по региону
    :return: Таблицу с общей статистикой по региону для отображения на странице
    '''
    df = pd.DataFrame(
        data={
            'Показатель': region_dict.keys(),
            'Значения': region_dict.values()
        }
    )

    table = dash.dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        style_cell={'textAlign': 'left'},
    )

    return table

def generate_region_cities_layout_enrolled(region_c_df: pd.DataFrame):
    '''
    Генерация таблицы со статистикой
    :param region_c_df: Датафрейм со статистикой по города
    :return: Табличку со статистикой для отображения на странице
    '''
    table = dash.dash_table.DataTable(
        data=region_c_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in region_c_df.columns],
        style_cell={'textAlign': 'left'},
        sort_action="native",
        page_size=15
    )

    return table

def get_region_stats_by_id_enrolled(region_id):
    '''

    :param region_id: Код региона
    :return: Словарь со статистикой по региону
    '''
    reg_stats: pd.DataFrame = reg_df[reg_df['Код региона'] == region_id]
    reg_dict = reg_stats.to_dict('records')[0].copy()
    del reg_dict['Код региона'], reg_dict['Тип региона']
    return reg_dict

def get_region_cities_stats_by_id_enrolled(region_id):
    '''
    Получения статистики по всем городам региона
    :param region_id: Код региона
    :return: Датафрейм со статистикой по региону, отсортированно по кол-ву зачисленных
    '''
    reg_c_df = city_df[city_df['Код региона'] == region_id]
    reg_c_df = reg_c_df.drop(
        labels=['Код региона', 'Название региона', 'Тип региона'], axis=1
    )
    reg_c_df = reg_c_df.dropna()

    reg_c_df = reg_c_df.sort_values(by='Поступило', ascending=False)

    return reg_c_df

external_stylesheets = [dbc.themes.GRID,
                        dbc.themes.BOOTSTRAP,
                        'https://codepen.io/chriddyp/pen/bWLwgP.css'
                        ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=0.7'}])
server = app.server

enrolled_classes = [0, 10, 20, 50, 100, 200, 500, 1000] # Отсечки для категорий зачисленных
enrolled_colorscale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'] # Цвета для зачисленных
style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.7)
enrolled_ctg = ["{}+".format(cls, enrolled_classes[i + 1]) for i, cls in enumerate(enrolled_classes[:-1])] + ["{}+".format(enrolled_classes[-1])] # Категории для зачисленных
enrolled_colorbar = dlx.categorical_colorbar(categories=enrolled_ctg, colorscale=enrolled_colorscale, width=300, height=30, position="bottomleft") # Цветовая карта для зачисленных
# Функия на ЖС для определения цвета на стороне браузера
style_handle = assign("""function(feature, context){
    const {classes, colorscale, style, colorProp} = context.props.hideout;  // get props from hideout
    const value = feature.properties[colorProp];  // get value the determines the color
    for (let i = 0; i < classes.length; ++i) {
        if (value > classes[i]) {
            style.fillColor = colorscale[i];  // set the fill color according to the class
        }
    }
    return style;
}""")

# Создание общего жсона. При необходимости подменяется параметр hideout в колбэке(наверное)
geojson = dl.GeoJSON(data=GEO_DATA,  # url to geojson file
                     options=dict(style=style_handle),  # how to style each polygon
                     zoomToBounds=True,  # when true, zooms to bounds when data changes (e.g. on load)
                     hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
                     hideout=dict(colorscale=enrolled_colorscale, classes=enrolled_classes, style=style, colorProp="enrolled"),
                     id="regions")
info = html.Div(children=get_enrolled_info_on_hover(), id="info", className="info",
                style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000"})

app.layout = dbc.Container(children=[
    dcc.Dropdown(
        options={1: 'Целевое', 2: 'Зачисленные'}, multi=False, clearable=False, id='type_stat', value=2
    ),
    dbc.Modal(children=[
        dbc.ModalHeader(dbc.ModalTitle(id='regio_modal_title')),
        dbc.ModalBody(id='regio_modal_body')
    ], id='regio_modal', is_open=False, fullscreen=True),
    html.Br(),
    dl.Map(center=[65, 70], zoom=3, children=[dl.TileLayer(url='https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png'),
                                              geojson,
                                              enrolled_colorbar,
                                              info
                                              ], style={'width': '100%', 'height': '90vh', 'margin': "auto", "display": "block"}, id="map"),
    html.Div(id="state"), html.Div(id="capital")
], fluid='sm')#style={'marginLeft': 250, 'marginRight': 250})

@app.callback(
    [Output("regio_modal", "is_open"),
     Output("regio_modal_title", 'children'), Output('regio_modal_body', 'children'),
     Output("regions", "click_feature") # Нужно обязательно, так как дэш не обработает вызов с теми же аргументами
     ],
    [Input("regions", "click_feature")],
    [State('regio_modal', 'is_open'), State("type_stat", "value")]
)
def show_modal(feature, is_open, type_stat):
    if not feature:
        raise dash.exceptions.PreventUpdate

    reg_id = feature['properties']['id']
    if type_stat == 2:
        reg_stats = get_region_stats_by_id_enrolled(reg_id)
        reg_name = reg_stats['Название региона']
        del reg_stats['Название региона']
        reg_total_table = generate_region_total_layout_enrolled(reg_stats)
        reg_c_df = get_region_cities_stats_by_id_enrolled(reg_id)
        reg_c_table = generate_region_cities_layout_enrolled(reg_c_df)
        lout = html.Div(
            children=[
                reg_total_table,
                html.Br(),
                html.H4('Статистика по городам'),
                reg_c_table
            ]
        )
        return not is_open, reg_name, lout, None


@app.callback(Output("info", "children"), [Input("regions", "hover_feature")])
def info_hover(feature):
    return get_enrolled_info_on_hover(feature)

if __name__ == '__main__':
    pass
    app.run(debug=True)