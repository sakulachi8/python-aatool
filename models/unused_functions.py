#######################################
# Colour buttons
#######################################

theme_colors = [
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
    "info",
    "light",
    "dark",
    "link",
]


def create_colors(theme_colors):
    colors = html.Div(
        [
            dbc.Button(f"{color}", color=f"{color}", size="sm")
            for color in theme_colors
        ]
    )
    return html.Div(["Theme Colors:", colors], className="mt-2")

colors = create_colors(theme_colors)