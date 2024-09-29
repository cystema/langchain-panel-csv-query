import panel as pn
from langchain.llms import OpenAI
from langchain_experimental.agents.agent_toolkits.csv.base import create_csv_agent
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import io
import os
import warnings

# Initialize Panel extension
warnings.filterwarnings('ignore')
pn.extension('plotly', 'tabulator')
load_dotenv()

# Set your OpenAI API key
OPENAI_API_KEY=""

file_name = "./data.csv"
data = pd.read_csv(file_name).drop(columns=['id'])
plot_pane = pn.pane.Plotly(sizing_mode="stretch_width")

file_input = pn.widgets.FileInput()
text_input = pn.widgets.TextInput(name='Question', placeholder='Ask a question from the CSV', sizing_mode='stretch_width')
ask_button = pn.widgets.Button(name="Ask", button_type="primary", height=60)

load_button = pn.widgets.Button(name="Load", button_type="primary")
# Removed plot_button as it's optional with event watchers

chat_box = pn.widgets.ChatBox(
    value=[],
    message_hue=220,
    ascending=True,
    allow_input=False
)

def load_page(data, file_name):
    target = data.columns[-1]
    numeric_columns = list(data._get_numeric_data().columns)

    yaxis = pn.widgets.Select(
        name='Y axis',
        options=numeric_columns,
        value=numeric_columns[1] if len(numeric_columns) > 1 else numeric_columns[0]
    )
    xaxis = pn.widgets.Select(
        name='X axis',
        options=numeric_columns,
        value=numeric_columns[0]
    )
    plot = px.scatter(data, x=xaxis.value, y=yaxis.value, color=target)
    table = pn.widgets.Tabulator(data)
    agent = create_csv_agent(
        OpenAI(model="gpt-3.5-turbo-instruct", temperature=0, openai_api_key=OPENAI_API_KEY),
        file_name,
        verbose=True,
        return_intermediate_steps=True
    )

    return target, yaxis, xaxis, plot, table, agent

target, yaxis, xaxis, plot, table, agent = load_page(data, file_name)
plot_pane.object = plot

# Set up event watchers for axis widgets
def update_plot(event):
    new_plot = px.scatter(data, x=xaxis.value, y=yaxis.value, color=target)
    plot_pane.object = new_plot

xaxis.param.watch(update_plot, 'value')
yaxis.param.watch(update_plot, 'value')

template = pn.template.FastListTemplate(
    title='CSV Analyzer',
    sidebar=[
        pn.pane.Markdown("# Analyze your CSVs"),
        pn.pane.Markdown("## Settings"),
        pn.Row(file_input, load_button),
        yaxis,
        xaxis,
        plot_pane
    ],
    main=[
        table,
        pn.Row(text_input, ask_button),
        chat_box
    ],
    sidebar_width=420,
    accent_base_color="#88d8b0",
    header_background="#88d8b0"
)

def parse_file_input(event):
    global data, file_name, target, yaxis, xaxis, table, agent

    value = file_input.value
    bytes_io = io.BytesIO(value)
    data = pd.read_csv(bytes_io)
    file_name = file_input.filename
    data.to_csv(file_name, index=False)

    target, yaxis, xaxis, plot, table, agent = load_page(data, file_name)
    plot_pane.object = plot

    # Update the components in the template
    template.main[0] = table
    template.sidebar[3] = yaxis
    template.sidebar[4] = xaxis

    # Reassign event watchers for new widgets
    xaxis.param.watch(update_plot, 'value')
    yaxis.param.watch(update_plot, 'value')

load_button.on_click(parse_file_input)

def ask(event):
    query = text_input.value
    chat_box.append({"User": query})
    response = agent({"input": query})
    chat_box.append({"Thought Process": [x[0].log for x in response["intermediate_steps"]]})
    chat_box.append({"Bot": response['output']})

ask_button.on_click(ask)

# Serve the app
template.show(
    open=False,
    address='0.0.0.0',
    port=8080,
    allow_websocket_origin=['*']
)