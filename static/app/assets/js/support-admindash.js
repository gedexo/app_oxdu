"use strict"

/* Gender by Employee Chart */

var options = {
    series: [64, 45],
    labels: ["New Tickets", "Closed Tickets"],
    chart: {
        height: 278,
        type: 'donut',
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false,
    },

    legend: {
        show: false,
    },
    stroke: {
        show: true,
        curve: 'smooth',
        lineCap: 'round',
        colors: "#fff",
        width: 0,
        dashArray: 0,
    },
    plotOptions: {

        pie: {
            expandOnClick: false,
            donut: {
                size: '80%',
                background: 'transparent',
                labels: {
                    show: true,
                    name: {
                        show: true,
                        fontSize: '20px',
                        color: '#495057',
                        offsetY: -4
                    },
                    value: {
                        show: true,
                        fontSize: '18px',
                        color: undefined,
                        offsetY: 8,
                        formatter: function (val) {
                            return val + "%"
                        }
                    },
                    total: {
                        show: true,
                        showAlways: true,
                        label: 'Total',
                        fontSize: '22px',
                        fontWeight: 600,
                        color: '#495057',
                    }

                }
            }
        }
    },
    colors: ["rgb(51, 102, 255)", "rgb(254, 127, 0)"],

};
document.querySelector("#Ticket-Statistics").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#Ticket-Statistics"), options);
chart.render();
function TicketStatistics() {
    chart.updateOptions({
        colors: ["rgb(" + myVarVal + ")", "rgb(254, 127, 0)"],
    })
};
/* Gender by Employee Chart */