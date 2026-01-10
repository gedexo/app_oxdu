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
                    offsetY: 3,
                    color: "#4b9bfa",
                    fontSize: ".825rem",
                    fontFamily: "Roboto",
                    fontWeight: 400,
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
    grid: {
        padding: {
          bottom: -8,
          top: -15,
        },
    },
    stroke: {
        lineCap: "round"
    },
    labels: ['09:00 hrs'],
};
document.querySelector("#attendance-details2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details2"), options);
chart.render();
/* attendance-details2 chart*/

/* attendance-details3 chart*/
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
document.querySelector("#attendance-details3").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details3"), options);
chart.render();
/* attendance-details3 chart*/

/* attendance-details4 chart*/
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
document.querySelector("#attendance-details4").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details4"), options);
chart.render();
/* attendance-details4 chart*/

(function () {
    "use strict"

let checkAll = document.querySelector('.check-all');
    checkAll.addEventListener('click', checkAllFn)

    function checkAllFn() {
        if (checkAll.checked) {
            document.querySelectorAll('.task-checkbox input').forEach(function (e) {
                e.closest('.task-list').classList.add('selected');
                e.checked = true;
            });
        }
        else {
            document.querySelectorAll('.task-checkbox input').forEach(function (e) {
                e.closest('.task-list').classList.remove('selected');
                e.checked = false;
            });
        }
    }
})();
