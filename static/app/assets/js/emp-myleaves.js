/* leaves overview */
var options = {
    series: [14, 8, 20, 18],
    labels: ["Casual Leaves","Sick Leaves", "Gifted Leaves", "Remaining Leaves"],
    chart: {
        height: 270,
        type: 'donut',
    },
    dataLabels: {
        enabled: false,
    },

    legend: {
        show: false,
		position: "bottom",
		horizontalAlign: "center",
		offsetY: 8,
		fontWeight: "bold",
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
            donut: {
                size: '85%',
                background: 'transparent',
                labels: {
                    show: true,
                    name: {
                        show: true,
                        fontSize: '29px',
                        color:'#6c6f9a',
                        offsetY: -10
                    },
                    value: {
                        show: true,
                        fontSize: '26px',
                        color: undefined,
                        offsetY: 16,
                    },
                    total: {
                        show: true,
                        showAlways: false,
                        label: 'Total Leaves',
                        fontSize: '22px',
                        fontWeight: 600,
                        color: '#373d3f',
                    }

                }
            }
        }
    },
    colors: ["rgba(51, 102, 255, 1)", "rgba(247, 40, 74, 1)", "rgba(254, 127, 0, 1)", "rgba(1, 195, 83, 1)"],
};
document.querySelector("#leavesoverview").innerHTML = " ";
var chart2 = new ApexCharts(document.querySelector("#leavesoverview"), options);
chart2.render();
function leavesOverview() {
    chart2.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(247, 40, 74, 1)", "rgba(254, 127, 0, 1)", "rgba(1, 195, 83, 1)"],
    })
};
/* leaves overview */


    /* For Date Range Picker */
    flatpickr("#daterange", {
        mode: "range",
        dateFormat: "Y-m-d",
    });
