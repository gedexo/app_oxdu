/* Profits Earned Chart */
var options1 = {
    series: [{
        name: 'Profit Earned',
        data: [44, 42, 57, 86, 58, 55, 70,44, 42, 57, 86, 58],
    }, {
        name: 'Total Sales',
        data: [40, 38, 47, 86, 51, 55, 65,39, 32, 47, 76, 41],
    }],
    chart: {
        type: 'bar',
        height: 355,
        toolbar: {
            show: false,
        }
    },
    grid: {
        borderColor: '#f1f1f1',
        strokeDashArray: 3
    },
    colors: ["rgb(51, 102, 255)", "#e4e7ed"],
    plotOptions: {
        bar: {
            columnWidth: '50%',
            borderRadius: 5,
        }
    },
    dataLabels: {
        enabled: false,
    },
    stroke: {
        show: true,
        width: 2,
    },
    legend: {
        show: false,
        position: 'top',
    },
    yaxis: {
        title: {
            style: {
                color: '#adb5be',
                fontSize: '13px',
                fontFamily: 'poppins, sans-serif',
                fontWeight: 600,
                cssClass: 'apexcharts-yaxis-label',
            },
        },
        labels: {
            formatter: function (y) {
                return y.toFixed(0) + "";
            }
        }
    },
    xaxis: {
        type: 'week',
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        axisBorder: {
            show: true,
            color: 'rgba(119, 119, 142, 0.05)',
            offsetX: 0,
            offsetY: 0,
        },
        axisTicks: {
            show: true,
            borderType: 'solid',
            color: 'rgba(119, 119, 142, 0.05)',
            width: 6,
            offsetX: 0,
            offsetY: 0
        },
        labels: {
            rotate: -90
        }
    }
};
document.getElementById('chartbar-statistics').innerHTML = '';
var chart1 = new ApexCharts(document.querySelector("#chartbar-statistics"), options1);
chart1.render();

function chartbarstatistics() {
    chart1.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(" + myVarVal + ", 0.2)"],
    });
}
/* Profits Earned Chart */
/* Gender by Employee Chart */
var options = {
    series: [80, 29, 50],
    labels: ["Design", "Service","Development"],
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
                        // color: '#495057',
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
                        showAlways: false,
                        label: 'Total Analysis',
                        fontSize: '18px',
                        fontWeight: 400,
                    }

                }
            }
        }
    },
    colors: ["rgba(51, 102, 255, 1)", "rgba(254, 127, 0, 1)"],
};
document.querySelector("#analysis").innerHTML = " ";
var chart2 = new ApexCharts(document.querySelector("#analysis"), options);
chart2.render();
function analysis() {
    chart2.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(254, 127, 0, 1)","#0dcd94"],
    })
};
/* Gender by Employee Chart */
// Career Page Stats
var options = {
	series: [ {
		name: 'Accepted',
		type: 'line',
		data: [15, 32, 15, 38, 18, 25]
	},
	{
		name: 'Rejected',
		type: 'area',
		data: [25, 28, 21, 33, 18, 36]
	}],
	chart: {
	height: 190,
	fontFamily: 'Poppins, Arial, sans-serif',
	toolbar: {
		show: false
	}
	},
	grid: {
	show: false,
	borderColor: '#f2f6f7',
	},
	dataLabels: {
	enabled: false
	},
	legend: {
	show: false,
	position: 'top',
	fontSize: '13px',
	},
	stroke: {
	width: [3,3],
	curve: 'smooth',
	},
	plotOptions: {
		bar: {
			columnWidth: "27%",
			borderRadius: 1
		}
	},
	labels: ['2015', '2016', '2017', '2018', '2019','2020'],
};
var chart3 = new ApexCharts(document.querySelector("#expenses"), options);
chart3.render();

function expenses(){
	chart3.updateOptions({
		colors: ["rgba(" + myVarVal + ", 0.99)","rgba(" + myVarVal + ", 0.2)"],
	})
};

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
    labels: ["75%"]
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
    labels: ["38%"]
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
    labels: ["67%"]
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
    colors: ["#f34932"],
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
                    colors: "#f34932"
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
    labels: ["49%"]
};
document.querySelector("#attendance4").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance4"), options);
chart.render();
/* attendance chart4*/


/* For Inline Calendar */
flatpickr("#calendar", {
    inline: true
});

(function () {
    "use strict"


  /* multi select with remove button */
  const multipleCancelButton = new Choices(
    '#choices-multiple-remove-button',
    {
      allowHTML: true,
      removeItemButton: true,
    }
  );

})();
