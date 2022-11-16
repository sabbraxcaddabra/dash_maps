import dash
from dash import dcc, html, Output, Input, State
import dash_bootstrap_components as dbc
import os
import pandas as pd

HERE = os.path.dirname(__file__)
REGIONS_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, ".", "regi.csv")))
CITIES_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, ".", "cities.csv")))

reg_df = pd.read_csv(REGIONS_FILE)
city_df = pd.read_csv(CITIES_FILE)

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
        page_size=10
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

app.layout = dbc.Container(children=[
    dcc.Dropdown(
        options={1: 'Целевое', 2: 'Зачисленные'}, multi=False, clearable=False, id='type_stat', value=2
    ),
    dbc.Modal(children=[
        dbc.ModalHeader(dbc.ModalTitle(id='regio_modal_title')),
        dbc.ModalBody(id='regio_modal_body')
    ], id='regio_modal', fullscreen=True),
    dbc.Button(id='submit', children='Отобразить статистику'),
], fluid='sm')#style={'marginLeft': 250, 'marginRight': 250})

@app.callback(
    [Output("regio_modal", "is_open"), Output("regio_modal_title", 'children'), Output('regio_modal_body', 'children')],
    [Input('submit', "n_clicks")],
    [State('regio_modal', 'is_open'), State("type_stat", "value")]
)
def show_modal(n, is_open, type_stat):
    if n is None:
        raise dash.exceptions.PreventUpdate
    else:
        if type_stat == 2:
            reg_stats = get_region_stats_by_id_enrolled(59)
            reg_name = reg_stats['Название региона']
            del reg_stats['Название региона']
            reg_total_table = generate_region_total_layout_enrolled(reg_stats)
            reg_c_df = get_region_cities_stats_by_id_enrolled(59)
            reg_c_table = generate_region_cities_layout_enrolled(reg_c_df)
            lout = html.Div(
                children=[
                    reg_total_table,
                    html.Br(),
                    html.H4('Статистика по городам'),
                    reg_c_table
                ]
            )
            return not is_open, reg_name, lout

if __name__ == '__main__':
    app.run(debug=True)