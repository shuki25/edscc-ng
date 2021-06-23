import json
import logging

from django import http
from django.views.generic import TemplateView

log = logging.getLogger(__name__)

COLORS1 = [
    (0, 123, 255),  # primary, blue
    (108, 117, 125),  # secondary, gray
    (40, 167, 69),  # success, green
    (23, 162, 184),  # info, cyan
    (255, 193, 7),  # warning, yellow
    (220, 53, 69),  # danger, red
    (102, 16, 242),  # indigo
    (253, 126, 20),  # orange
    (32, 201, 151),  # teal
    (1, 255, 112),  # lime
    (232, 62, 140),  # pink
    (0, 31, 63),  # navy
]

COLORS = [
    (88, 153, 218),
    (232, 116, 59),
    (25, 169, 121),
    (237, 74, 123),
    (148, 94, 207),
    (19, 164, 180),
    (82, 93, 244),
    (191, 57, 158),
    (108, 136, 147),
    (238, 104, 104),
    (47, 100, 151),
]


def next_color(color_list=None):
    """Create a different color from a base color list."""
    if color_list is None:
        color_list = COLORS
    step = 0
    while True:
        for color in color_list:
            yield list(map(lambda base: (base + step) % 256, color))
        step += 197


class ComplexEncoder(json.JSONEncoder):
    """Always return JSON primitive."""

    def default(self, obj):
        try:
            return super(ComplexEncoder, obj).default(obj)
        except TypeError:
            if hasattr(obj, "pk"):
                return obj.pk
            return str(obj)


class JSONResponseMixin(object):
    def render_to_response(self, context):
        """Returns a JSON response containing 'context' as payload"""
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        """Construct an `HttpResponse` object."""
        return http.HttpResponse(
            content, content_type="application/json", **httpresponse_kwargs
        )

    def convert_context_to_json(self, context):
        """Convert the context dictionary into a JSON object"""
        return json.dumps(context, cls=ComplexEncoder)


class JSONView(JSONResponseMixin, TemplateView):
    """A Base JSON View using the Mixin."""

    pass


class ChartMixinView(JSONView):
    def get_context_data(self, **kwargs):
        context = super(ChartMixinView, self).get_context_data(**kwargs)
        context.update(
            {
                "labels": self.get_labels(),
                "datasets": self.get_datasets(),
            }
        )
        return context

    def get_colors(self):
        return next_color()

    def get_dataset_options(self, **kwargs):
        default_options = {}
        default_options.update(kwargs)
        return default_options

    def get_datasets(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_labels(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_data(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a data list list. " "(i.e: [[25, 34, 0, 1, 50], ...])."
        )


class ChartLineView(ChartMixinView):
    def get_labels(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_data(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a data list list. " "(i.e: [[25, 34, 0, 1, 50], ...])."
        )

    def get_dataset_options(self, **kwargs):
        options = super(ChartLineView, self).get_dataset_options(**kwargs)
        # log.debug("kwargs=%s" % kwargs)
        if "color" in kwargs:
            color = kwargs["color"]
            options.update(
                {
                    "backgroundColor": "rgba(%d, %d, %d, 0.5)" % color,
                    "borderColor": "rgba(%d, %d, %d, 1)" % color,
                    "pointBackgroundColor": "rgba(%d, %d, %d, 1)" % color,
                    "pointBorderColor": "#fff",
                }
            )
        return options

    def get_datasets(self):
        datasets = []
        color_generator = self.get_colors()
        data = self.get_data()
        providers = self.get_providers()
        num = len(providers)
        for i, entry in enumerate(data):
            color = tuple(next(color_generator))
            dataset = {"data": entry}
            dataset.update(self.get_dataset_options(color=color))
            if i < num:
                dataset["label"] = providers[i]  # series labels for Chart.js
            datasets.append(dataset)
        return datasets

    def get_providers(self):
        return []


class ChartPieView(ChartMixinView):
    def get_labels(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_data(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a data list list. " "(i.e: [[25, 34, 0, 1, 50], ...])."
        )

    def get_dataset_options(self, **kwargs):
        options = super(ChartPieView, self).get_dataset_options(**kwargs)
        options.update(
            {
                "hoverOffset": 4,
            }
        )
        return options

    def get_datasets(self):
        datasets = []
        background_color = []
        color_generator = self.get_colors()
        data = self.get_data()
        for i, entry in enumerate(data):
            color = tuple(next(color_generator))
            background_color.append("rgb(%d, %d, %d)" % color)
        dataset = {"data": data}
        dataset.update(self.get_dataset_options(backgroundColor=background_color))
        datasets.append(dataset)
        return datasets


class ChartDoughnutView(ChartPieView):
    def get_labels(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_data(self):
        raise NotImplementedError(  # pragma: no cover
            "You should return a data list list. " "(i.e: [[25, 34, 0, 1, 50], ...])."
        )
