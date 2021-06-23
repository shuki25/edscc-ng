{% load i18n gravatar account humanize static %}
{% get_current_language as LANGUAGE_CODE %}
$.get('{% url chart_url report_id %}', function (data) {
    var ctx = $("#{{ chart_id }}").get(0).getContext("2d");
    new Chart(ctx, {
        type: '{{ type }}',
        data: data,
        options: {
            layout: {
                padding: 5,
            },
            animation: {
                easing: "easeInCubic",
                duration: 1000
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 20,
                    },
                },
                title: {
                    padding: 0,
                },
                maintainAspectRatio: true
            },
        }
    });
});
