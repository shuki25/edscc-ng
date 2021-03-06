{% load i18n gravatar account humanize static %}
{% get_current_language as LANGUAGE_CODE %}
$.get('{% url chart_url report_id %}', function (data) {
    const COLOR = "white";
    var ctx = $("#{{ chart_id }}").get(0).getContext("2d");
    new Chart(ctx, {
        type: '{{ type }}',
        data: data,
        options: {
            animation: {
                easing: "easeInCubic",
                duration: 500
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
            },
            plugins: {
                tooltip: {
                    enabled: true,
                    intersect: false,
                    callbacks: {
                        title: function (context) {
                            return "{% trans 'Total Earning on' %} " + context[0].label;
                        },
                        label: function (context) {
                            return context.dataset.label + ": " + context.formattedValue;
                        },
                    },
                },
                legend: {
                    display: true,
                    labels: {
                        boxWidth: 20,
                        color: COLOR,
                    },
                },
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        color: COLOR,
                        text: "{% trans 'Credits' %}",
                    },
                    stacked: false,
                    ticks: {
                        color: COLOR,
                        callback: function (value, index, ticks) {
                            return value.toLocaleString(locale = "{{ LANGUAGE_CODE }}");
                        }
                    }
                },
                x: {
                    ticks: {
                        color: COLOR,
                        callback: function (value, index, ticks) {
                            return this.getLabelForValue(value).toLocaleString(locale = "{{ LANGUAGE_CODE }}");
                        }
                    }
                }
            },
            maintainAspectRatio: false
        }
    });
});
