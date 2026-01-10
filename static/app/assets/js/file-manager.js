/* storage-data chart*/
var options = {
    chart: {
        height: 120,
        width: 90,
        type: "radialBar",
    },

    series: [85],
    colors: ["rgba(51, 102, 255, 1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "50%",
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
document.querySelector("#storage-data").innerHTML = " ";
var chart = new ApexCharts(document.querySelector("#storage-data"), options);
chart.render();
function Storagedata() {
    chart.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)"],
    })
};
/* storage-data chart*/