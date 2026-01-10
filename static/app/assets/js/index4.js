(function () {
    "use strict"

/* attendance chart*/
var options = {
    chart: {
        height: 100,
        width: 60,
        type: "radialBar",
    },

    series: [75],
    colors: ["#0dcd94"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ['75'],
};
document.querySelector("#attendance").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance"), options);
chart.render();
/* attendance chart*/

/* attendance chart2*/
var options = {
    chart: {
        height: 100,
        width: 60,
        type: "radialBar",
    },

    series: [38],
    colors: ["rgba(51,102,255,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["38"]
};
document.querySelector("#attendanc2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendanc2"), options);
chart.render();
/* attendance chart2*/

/* attendance chart3*/
var options = {
    chart: {
        height: 100,
        width: 60,
        type: "radialBar",
    },

    series: [67],
    colors: ["#ffad00"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["67"]
};
document.querySelector("#attendance3").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance3"), options);
chart.render();
/* attendance chart3*/

/* attendance chart4*/
var options = {
    chart: {
        height: 100,
        width: 60,
        type: "radialBar",
    },

    series: [49],
    colors: ["#0fcd95"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["49"]
};
document.querySelector("#attendance4").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance4"), options);
chart.render();
/* attendance chart4*/

})();

/* Revenue Analytics Chart */
var options = {
    series: [
        {
            type: 'line',
            name: 'Profit',
            data: [
                {
                    x: 'Jan',
                    y: 100
                },
                {
                    x: 'Feb',
                    y: 210
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
                    y: 610
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
            name: 'Revenue',
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
                    y: 320
                },
                {
                    x: 'Mar',
                    y: 376
                },
                {
                    x: 'Apr',
                    y: 220
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
            name: 'Sales',
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
                    y: 200
                },
                {
                    x: 'Feb',
                    y: 530
                },
                {
                    x: 'Mar',
                    y: 110
                },
                {
                    x: 'Apr',
                    y: 130
                },
                {
                    x: 'May',
                    y: 480
                },
                {
                    x: 'Jun',
                    y: 520
                },
                {
                    x: 'Jul',
                    y: 780
                },
                {
                    x: 'Aug',
                    y: 435
                },
                {
                    x: 'Sep',
                    y: 475
                },
                {
                    x: 'Oct',
                    y: 738
                },
                {
                    x: 'Nov',
                    y: 454
                },
                {
                    x: 'Dec',
                    y: 480
                }
            ]
        }
    ],
    chart: {
        height: 350,
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
    colors: ["rgb(51, 102, 255)", "#fe7f00", "rgba(119, 119, 142, 0.05)"],
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
        dashArray: [0, 0, 0],
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
    title: {
        show: false
    },
    markers: {
        hover: {
            sizeOffset: 5
        }
    }
};

document.getElementById('balance').innerHTML = '';
var chart = new ApexCharts(document.querySelector("#balance"), options);
chart.render();
console.log(chart);

function revenueAnalytics() {
    chart.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "#fe7f00", "rgba(" + myVarVal + ", 0.05)"],
    })
}

/* Revenue Analytics Chart */


/* Gender by Employee Chart */
var options = {
    series: [80, 29],
    labels: ["Male", "Female"],
    chart: {
        height: 310,
        type: 'donut',
    },
    dataLabels: {
        enabled: false,
    },

    legend: {
        show: true,
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
                        color: '#495057',
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
                        label: 'Total Employees',
                        fontSize: '16px',
                        fontWeight: 400,
                        // color: '#495057',
                    }

                }
            }
        }
    },
    colors: ["rgba(51, 102, 255, 1)", "rgba(254, 127, 0, 1)"],
};
document.querySelector("#employees").innerHTML = " ";
var chart2 = new ApexCharts(document.querySelector("#employees"), options);
chart2.render();
function Employees() {
    chart2.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(254, 127, 0, 1)"],
    })
};
/* Gender by Employee Chart */

/* progress chart*/
var options = {
    chart: {
        height: 90,
        width: 60,
        type: "radialBar",
    },

    series: [75],
    colors: ["#0dcd94"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".7rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["75"]
};
document.querySelector("#progress").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#progress"), options);
chart.render();
/* progress chart*/
/* progress2 chart*/
var options = {
    chart: {
        height: 90,
        width: 60,
        type: "radialBar",
    },

    series: [75],
    colors: ["#3366ff"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".7rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["75"]
};
document.querySelector("#progress2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#progress2"), options);
chart.render();
/* progress2 chart*/

/* progress3 chart*/
var options = {
    chart: {
        height: 90,
        width: 60,
        type: "radialBar",
    },

    series: [75],
    colors: ["#fe7f00"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "40%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 4,
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 500,
                    colors: "#4b9bfa"
                },
                value: {
                    offsetY: 5,
                    color: "#fe7f00",
                    fontSize: ".7rem",
                    show: false,
                    fontWeight: 500
                }
            }
        }
    },
    states: {
		normal: {
			filter: {
				type: 'none',
			}
		},
		hover: {
			filter: {
				type: 'none',
			}
		},
		active: {
			filter: {
				type: 'none',
			}
		},
	},
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ["75"]
};
document.querySelector("#progress3").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#progress3"), options);
chart.render();
/* progress3 chart*/


    /* For Inline Calendar */
    flatpickr("#calendar", {
        inline: true
    });
