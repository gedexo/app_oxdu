/* attendance chart*/
var options = {
    chart: {
        height: 127,
        width: 100,
        type: "radialBar",
    },

    series: [89],
    colors: ["rgba(51,102,255,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "52%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    fontWeight: 400,
                    fontFamily: 'Roboto',
                    show: true
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
    labels: ["89"]
};
document.querySelector("#attendance").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance"), options);
chart.render();
/* attendance chart*/

/* projects1 chart*/
var options = {
    chart: {
        height: 127,
        width: 100,
        type: "radialBar",
    },

    series: [23],
    colors: ["rgba(254,127,0,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "52%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    fontWeight: 400,
                    fontFamily: 'Roboto',
                    show: true
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
    labels: ["23"]
};
document.querySelector("#projects1").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#projects1"), options);
chart.render();
/* projects1 chart*/

/* performance chart*/
var options = {
    chart: {
        height: 127,
        width: 100,
        type: "radialBar",
    },

    series: [67],
    colors: ["rgba(13,205,148,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "52%",
                background: "#fff"
            },
            dataLabels: {
                name: {
                    offsetY: 5,
                    color: "#4b9bfa",
                    fontSize: ".875rem",
                    fontWeight: 400,
                    fontFamily: 'Roboto',
                    show: true
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
document.querySelector("#performance").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#performance"), options);
chart.render();
/* performance chart*/