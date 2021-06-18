{% load i18n gravatar account humanize static %}
{% get_current_language as LANGUAGE_CODE %}
$.get('{% url chart_url report_id %}', function (data) {
    var ctx = $("#{{ chart_id }}").get(0).getContext("2d");
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            animation: {
                easing: "easeInCubic",
                duration: 500
            },
            tooltips: {
                enabled: true,
                mode: "x-axis",
                position: "nearest",
                callbacks: {
                    title: function (tooltipItems, data) {
                        return "{% trans 'Total Earning on' %} " + tooltipItems[0].xLabel;
                    },
                    label: function (tooltipItems, data) {
                        return data.datasets[tooltipItems.datasetIndex].label + ": " + tooltipItems.yLabel.toLocaleString(locale = "{{ LANGUAGE_CODE }}");
                    },
                    //                           footer: function (tooltipItems, data) {
                    //                               var numerator = parseInt(tooltipItems[0].yLabel);
                    //                               var denominator = parseInt(tooltipItems[1].yLabel);
                    //                               var delta_percent = ((numerator - denominator) / denominator) * 100;
                    //                               return "Percentage difference: " + delta_percent.toFixed(1) + "%";
                    //                           },
                }
            },
            legend: {
                display: true
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true
                },
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: "{% trans 'Credits' %}"
                    },
                    ticks: {
                        callback: function (value) {
                            return value.toLocaleString(locale = "{{ LANGUAGE_CODE }}");
                        }
                    }
                }],
                xAxes: [{
                    ticks: {
                        callback: function (value) {
                            return value.toLocaleString(locale = "{{ LANGUAGE_CODE }}");
                        }
                    }
                }]
            },
            maintainAspectRatio: true
        }
    });
});
