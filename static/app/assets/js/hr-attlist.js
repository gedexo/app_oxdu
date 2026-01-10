/* attendance-details chart*/
var options = {
    chart: {
        height: 170,
        type: "radialBar",
    },

    series: [50],
    colors: ["rgba(13,205,148,1)"],
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
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "65%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: -10,
                    color: "#4b9bfa",
                    fontSize: ".625rem",
                    show: false
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: true,
                    fontWeight: 500
                }
            }
        }
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
    labels: ["Status"]
};
document.querySelector("#attendance-details").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details"), options);
chart.render();
/* attendance-details chart*/

/* attendance-details2 chart*/
var options = {
    chart: {
        height: 170,
        type: "radialBar",
    },

    series: [100],
    colors: ["rgba(13,205,148,1)"],
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
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "65%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: -10,
                    color: "#4b9bfa",
                    fontSize: ".625rem",
                    show: false
                },
                value: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    show: true,
                    fontWeight: 500
                }
            }
        }
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
    labels: ["Status"]
};
document.querySelector("#attendance-details2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details2"), options);
chart.render();
/* attendance-details2 chart*/
