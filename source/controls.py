import ipywidgets as widgets
from ipywidgets import Layout

from source.table import build_query


class MyFilterWidget(widgets.Tab):
    def __init__(self, data):
        super(MyFilterWidget, self).__init__()

        self.selectors = dict()
        self.accordion = None
        self.query_text = None
        self.data = data
        self.out = None
        self.init_ui()

    def init_ui(self):
        # Initiate accordion with data selection widgets
        self.build_data_accordion()
        # Initiate text area for query string
        self.query_text = self.query_text_area()
        # Add accordion and text area to main Tab widget
        self.build_tabs()
        # Make query creation interactive by passing values from selection widgets
        self.out = widgets.interactive_output(self.populate_query_text_area, self.selectors)

    def populate_query_text_area(self, **args):
        """Create query interactively and write to query text area.
        Arguments:
            args -- Dictionary of tuple values from selection widgets
        """

        for child in self.accordion.children:
            if hasattr(child, "options"):
                if child.value == child.options:
                    del (args[child.description])

        query = build_query(args)
        self.query_text.value = query
        print(query)

    def build_data_accordion(self):
        """Create selection widgets and add to accordion view."""
        unique = self.get_unique_column_values()
        self.create_selectors(unique)

        self.accordion = widgets.Accordion([x for x in self.selectors.values()])
        for i, j in enumerate(self.selectors.keys()):
            self.accordion.set_title(i, j)
            self.accordion.set_title(i, j)

    @staticmethod
    def query_text_area():
        return widgets.Textarea(value=None,
                                placeholder="Enter your query here",
                                description="Query",
                                layout=Layout(width='80%', height='80px')
                                )

    @staticmethod
    def score_slider():
        slider = widgets.FloatRangeSlider(value=[0.0, +1.0],
                                          min=0.00, max=1, step=0.05,
                                          description='score',
                                          readout_format='.2f'
                                          )
        # Initialize options attribute with default values.
        # This allows us to filter out any default values when creating the filter query
        slider.options = slider.value
        return slider

    def create_selectors(self, unique):
        """Create selection items from column data.
        Arguments:
            unique -- Dictionary with column names as keys and unique values as values
        """

        for k, v in unique.items():
            items = sorted(v, key=lambda x: x.upper())
            # The value keyword argument is given all items as default.
            # This means that all values are selected/no filter applies.
            self.selectors[k] = widgets.SelectMultiple(options=items,
                                                       description=k, disabled=False,
                                                       rows=7, value=items, layout=Layout(width='80%')
                                                       )

        self.selectors['score'] = self.score_slider()

    def get_unique_column_values(self):
        """Get unique data from table columns with metadata."""

        cols = ["Relation", "Project", "Document", "s_lid", "t_lid"]
        d = {col: self.data[col].unique() for col in self.data[cols]}
        return d

    def build_tabs(self):
        """Add accordion widget and query text area to MyFilterWidget instance."""
        self.children = [self.accordion, self.query_text]
        self.set_title(0, "Data")
        self.set_title(1, "Python")

    def run_query(self):
        """Run query string to create a new slice of the data.

        Returns:
            data -- DataFrame object containing
        """
        # Get query string from the instance's query string area.
        query = self.children[1].value
        # Either pass the string to the DataFrame's query method or
        # create an identical copy of the DataFrame.
        if len(query) > 0:
            data = self.data.query(query).copy()
        else:
            data = self.data.copy()
        assert len(data) != 0, "Not enough data"

        return data
