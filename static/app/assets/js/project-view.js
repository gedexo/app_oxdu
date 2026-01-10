(function () {
    "use strict"

/* attendance chart*/
var options = {
    chart: {
        height: 90,
        width: 40,
        type: "radialBar",
    },

    series: [75],
    colors: ["#0dcd94"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "30",
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
                    fontSize: ".575rem",
                    show: true,
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
    labels: ["Status"]
};
document.querySelector("#attendance").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance"), options);
chart.render();
/* attendance chart*/

/* attendance chart2*/
var options = {
    chart: {
        height: 90,
        width: 40,
        type: "radialBar",
    },

    series: [38],
    colors: ["rgba(51,102,255,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "30",
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
                    fontSize: ".575rem",
                    show: true,
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
    labels: ["Status"]
};
document.querySelector("#attendanc2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendanc2"), options);
chart.render();
/* attendance chart2*/

/* attendance chart3*/
var options = {
    chart: {
        height: 90,
        width: 40,
        type: "radialBar",
    },

    series: [67],
    colors: ["#ffad00"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "30",
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
                    fontSize: ".575rem",
                    show: true,
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
    labels: ["Status"]
};
document.querySelector("#attendance3").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance3"), options);
chart.render();
/* attendance chart3*/

/* attendance chart4*/
var options = {
    chart: {
        height: 90,
        width: 40,
        type: "radialBar",
    },

    series: [49],
    colors: ["#0fcd95"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "30",
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
                    fontSize: ".575rem",
                    show: true,
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
    labels: ["Status"]
};
document.querySelector("#attendance4").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance4"), options);
chart.render();
/* attendance chart4*/

})();

 
 
 
(function () {
    "use strict"
        // for product features
        var toolbarOptions = [
            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
            [{ 'font': [] }],
            ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
            ['blockquote', 'code-block'],

            [{ 'header': 1 }, { 'header': 2 }],               // custom button values
            [{ 'list': 'ordered' }, { 'list': 'bullet' }],

            [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
            [{ 'align': [] }],
            ['clean']                                         // remove formatting button
        ];
        var quill = new Quill('#note', {
            modules: {
                toolbar: toolbarOptions
            },
            theme: 'snow'
        });


})();