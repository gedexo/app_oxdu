
/* Revenue Analytics Chart */
var options = {
    series: [
        {
            type: 'line',
            name: 'Applications',
            data: [
                {
                    x: 'Jan',
                    y: 100
                },
                {
                    x: 'Feb',
                    y: 510
                },
                {
                    x: 'Mar',
                    y: 180
                },
                {
                    x: 'Apr',
                    y: 354
                },
                {
                    x: 'May',
                    y: 230
                },
                {
                    x: 'Jun',
                    y: 320
                },
                {
                    x: 'Jul',
                    y: 656
                },
                {
                    x: 'Aug',
                    y: 510
                },
                {
                    x: 'Sep',
                    y: 350
                },
                {
                    x: 'Oct',
                    y: 350
                },
                {
                    x: 'Nov',
                    y: 210
                },
                {
                    x: 'Dec',
                    y: 410
                }
            ]
        },
        {
            type: 'line',
            name: 'Shortlisted',
            chart: {
                dropShadow: {
                    enabled: true,
                    enabledOnSeries: undefined,
                    top: 5,
                    left: 0,
                    blur: 3,
                    color: '#000',
                    opacity: 0.1
                }
            },
            data: [
                {
                    x: 'Jan',
                    y: 180
                },
                {
                    x: 'Feb',
                    y: 520
                },
                {
                    x: 'Mar',
                    y: 106
                },
                {
                    x: 'Apr',
                    y: 320
                },
                {
                    x: 'May',
                    y: 520
                },
                {
                    x: 'Jun',
                    y: 780
                },
                {
                    x: 'Jul',
                    y: 435
                },
                {
                    x: 'Aug',
                    y: 515
                },
                {
                    x: 'Sep',
                    y: 738
                },
                {
                    x: 'Oct',
                    y: 454
                },
                {
                    x: 'Nov',
                    y: 525
                },
                {
                    x: 'Dec',
                    y: 230
                }
            ]
        },
        {
            type: 'area',
            chart: {
                dropShadow: {
                    enabled: true,
                    enabledOnSeries: undefined,
                    top: 5,
                    left: 0,
                    blur: 3,
                    color: '#000',
                    opacity: 0.1
                }
            },
            data: [
                {
                    x: 'Jan',
                    y: 400
                },
                {
                    x: 'Feb',
                    y: 730
                },
                {
                    x: 'Mar',
                    y: 610
                },
                {
                    x: 'Apr',
                    y: 430
                },
                {
                    x: 'May',
                    y: 580
                },
                {
                    x: 'Jun',
                    y: 620
                },
                {
                    x: 'Jul',
                    y: 780
                },
                {
                    x: 'Aug',
                    y: 535
                },
                {
                    x: 'Sep',
                    y: 575
                },
                {
                    x: 'Oct',
                    y: 738
                },
                {
                    x: 'Nov',
                    y: 654
                },
                {
                    x: 'Dec',
                    y: 780
                }
            ]
        }
    ],
    chart: {
        height: 310,
        animations: {
            speed: 500
        },
        toolbar: {
            show: false,
        },
        dropShadow: {
            enabled: true,
            enabledOnSeries: undefined,
            top: 8,
            left: 0,
            blur: 3,
            color: '#000',
            opacity: 0.1
        },
    },
    colors: ["#3366ff", "rgba(51, 102, 255, 0.5)", "rgba(119, 119, 142, 0.05)"],
    dataLabels: {
        enabled: false
    },
    grid: {
        borderColor: '#f1f1f1',
        strokeDashArray: 3
    },
    stroke: {
        curve: 'smooth',
        width: [3, 3, 3],
        dashArray: [0, 6, 0],
    },
    xaxis: {
        axisTicks: {
            show: false,
        },
    },
    yaxis: {
        labels: {
            formatter: function (value) {
                return "$" + value;
            }
        },
    },
    tooltip: {
        y: [{
            formatter: function(e) {
                return void 0 !== e ? "$" + e.toFixed(0) : e
            }
        }, {
            formatter: function(e) {
                return void 0 !== e ? "$" + e.toFixed(0) : e
            }
        }, {
            formatter: function(e) {
                return void 0 !== e ? e.toFixed(0) : e
            }
        }]
    },
    legend: {
        show: false,
        customLegendItems: ['Profit', 'Revenue', 'Sales'],
        inverseOrder: true
    },
    toolbar: {
        show: false,
    },
    title: {
        show: false,
    },
    markers: {
        hover: {
            sizeOffset: 5
        }
    }
};

document.getElementById('statistics1').innerHTML = '';
var chart = new ApexCharts(document.querySelector("#statistics1"), options);
chart.render();
console.log(chart);

function statistics1() {
    chart.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(" + myVarVal + ", 0.5)", "rgba(" + myVarVal + ", 0.05)"],
    })
}

/* Revenue Analytics Chart */


/* Gender by Employee Chart */
var options = {
    series: [80, 29, 50, 30],
    labels: ["Applications", "Interviews", "Reject", "Hired"],
    chart: {
        height: 260,
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
		position: "bottom",
		horizontalAlign: "center",
		offsetY: 8,
		fontWeight: "normal",
		fontSize: '14px',

		markers: {
			width: 12,
			height: 12,
			strokeWidth: 0,
			strokeColor: '#fff',
			fillColors: undefined,
			radius: 4,
			customHTML: undefined,
			onClick: undefined,
			offsetX: 0,
			offsetY: 0
		},
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
                        color: '#6c6f9a',
                        offsetY: -13
                    },
                    value: {
                        show: true,
                        fontSize: '30px',
                        fontWeight: 500,
                        color: undefined,
                        offsetY: 8,
                        formatter: function (val) {
                            return val + "%"
                        }
                    },
                    total: {
                        show: true,
                        showAlways: true,
                        label: 'Total overview',
                        fontSize: '18px',
                        fontWeight: 400,
                        color: '#6c6f9a',
                    }

                }
            }
        }
    },
    colors: ["rgba(51, 102, 255, 1)", "rgba(254, 127, 0, 1)","#f7284a", "#0dcd94"],
};
document.querySelector("#overview").innerHTML = " ";
var chart2 = new ApexCharts(document.querySelector("#overview"), options);
chart2.render();
function overview() {
    chart2.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(254, 127, 0, 1)", "#f7284a", "#0dcd94"],
    })
};
/* Gender by Employee Chart */

/* For Inline Calendar */
flatpickr("#calendar", {
    inline: true
});