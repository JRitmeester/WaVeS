from sessions.session_manager import SessionManagerProtocol
from config.config_manager import ConfigManagerProtocol
from mapping.mapping_manager import MappingManagerProtocol
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui
from pathlib import Path
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from utils.utils import get_icon_path

class MappingDialog(QtWidgets.QWidget):
    def __init__(self, session_manager: SessionManagerProtocol, mapping_manager: MappingManagerProtocol, config_manager: ConfigManagerProtocol, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WaVeS - Mapping Diagram")
        self.setWindowIcon(QtGui.QIcon(get_icon_path().as_posix()))
        self.session_manager = session_manager
        self.mapping_manager = mapping_manager
        self.config_manager = config_manager

        # Set the background color to white
        self.setStyleSheet("background-color: white;")

        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.browser)
        self.resize(600, 400)
        self.show_graph()

    def show_graph(self):
        self.mappings = self.mapping_manager.get_mapping(self.session_manager, self.config_manager)
        
        # Transform the mappings into a dataframe
        rows = []
        for slider, sessions in self.mappings.items():
            for session in sessions:
                rows.append([slider, session.name])
        df = pd.DataFrame(rows, columns=["slider", "session"])

        # Create a sankey diagram
        # Create unique identifiers for sliders and sessions
        all_labels = list(df["slider"].unique()) + list(df["session"].unique())
        # Map each slider and session to its index in the all_labels list
        slider_indices = {slider: idx for idx, slider in enumerate(df["slider"].unique())}
        session_indices = {session: idx + len(slider_indices) for idx, session in enumerate(df["session"].unique())}
        
        # Map sources (sliders) and targets (sessions) to their indices
        sources = [slider_indices[slider] for slider in df["slider"]]
        targets = [session_indices[session] for session in df["session"]]
        
        fig = go.Figure(data=[go.Sankey(
            node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = all_labels,
                color = "black"
            ),
            link = dict(
                source = sources,
                target = targets,
                value = [1] * len(df)  # Equal weight for all connections
            )
        )])
        fig.update_traces(textfont_size=12)
        # Make the plot static
        fig.update_layout(
            hovermode=False,
            dragmode=False,
            clickmode='none',
            modebar=dict(remove=['zoom', 'pan', 'select', 'lasso', 'toImage', 'resetScale']),
            # Disable all interactivity
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            autosize=True,
            margin=dict(l=40, r=40, t=30, b=30)
        )
        
        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False, 'staticPlot': True}))