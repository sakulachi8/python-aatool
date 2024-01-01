import dash
from dash import html, dcc,Input,Output,State
import dash_bootstrap_components as dbc


app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.SPACELAB])

server = app.server

sidebar = dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active=True, id="home-link"),
                dbc.NavLink("Load Data", href="/load-data", id="load-data-link"),
                dbc.NavLink("Report", href="#", id="report-demo", active=False),
            ],
            vertical=True,
            pills=True,
            id="sidebar-hidden",
            className="bg-light"
)

mobile_navbar = dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.Div(page["name"], className="ms-2 md-4 nav-icon"),
                    ],
                    href="#" + page["path"] if page["name"] == "Reports" else page["path"],
                    active="exact",
                )
                for page in dash.page_registry.values()
            ],
             id="mobilebar-hidden",
)

topbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                
                dbc.Row(
                    [
                         dbc.Col(html.Img(src="/assets/logo.png", height="40px", style={'padding-left': '20px'})), # logo
                    ],
                    align="center",
                ),
                href="/",
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0, style={'float' : 'right'}),
            dbc.Collapse(
                mobile_navbar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
                
            ),
        ],
    ),
    color="primary",
    dark=True,
    expand="lg"
)




app.layout = dbc.Container([
    html.Link(
        rel='stylesheet',
        href='/assets/styles.css'
    ),
    topbar,
    html.Hr(),

    dbc.Row(
        [
            dbc.Col(
                [
                    dcc.Location(id='url'),
                    sidebar
                ], xs=0, sm=0, md=0, lg=2, xl=2, xxl=2),

            dbc.Col(
                [
                    
                    dash.page_container
                ], xs=12, sm=12, md=12, lg=10, xl=10, xxl=10)
        ]
    ),
    dcc.Store(id="data-store", data={}),
    dcc.Store(id="load-data-storage", data={}),
], fluid=True)

@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)

def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output('home-link', 'active'), Output('load-data-link', 'active') ,Output('report-demo', 'active')],
    Input('url', 'pathname')
)
def update_active_links(pathname):
    print(pathname)
    home_active = True if pathname == "/" else False
    load_data_active = True if pathname == "/load-data" else False
    reports_active = True if pathname == "/reports" else False
    return home_active, load_data_active ,reports_active

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
