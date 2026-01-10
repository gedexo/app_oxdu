/* overview budget Chart */
var options = {
	series: [{
		name: "Total Budget",
		data: [100, 300, 180, 680, 320, 560, 230, 800, 520, 220, 750, 210, 410]
	}, {
		name: "Total Employee",
		data: [200, 530, 110, 110, 480, 520, 780, 435, 475, 738, 454, 454, 230]
	}],
	chart: {
		height: 325,
		type: 'line',
		zoom: {
			enabled: false
		},
        toolbar: {
            show: false,
        },
		dropShadow: {
			enabled: true,
			enabledOnSeries: undefined,
			top: 5,
			left: 0,
			blur: 3,
			color: '#000',
			opacity: 0.1
		},
	},
	dataLabels: {
		enabled: false
	},
	legend: {
        show: false,
		position: "top",
		horizontalAlign: "center",
		offsetX: -15,
		fontWeight: "bold",
	},
	stroke: {
		curve: 'smooth',
		width: '3',
		dashArray: [0, 5],
	},
	grid: {
		borderColor: '#f2f6f7',
	},
	colors: ["rgb(98, 89, 202)", "rgba(98, 89, 202, 0.2)"],
	yaxis: {
		title: {
			text: '',
			style: {
				color: '#adb5be',
				fontSize: '14px',
				fontFamily: 'poppins, sans-serif',
				fontWeight: 500,
				cssClass: 'apexcharts-yaxis-label',
			},
		}
	},
	xaxis: {
		type: 'month',
		categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
		axisBorder: {
			show: false,
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
document.getElementById('overview-chart').innerHTML = ''
var chart1 = new ApexCharts(document.querySelector("#overview-chart"), options);
chart1.render();

function overView() {
	chart1.updateOptions({
		colors: ["rgb(" + myVarVal + ")", "rgba(" + myVarVal + ", 0.2)"],
	})
}
/* overview budget Chart */

/* Gender by Employee Chart */
var options = {
    series: [80, 29],
    labels: ["Male", "Female"],
    chart: {
        height: 329,
        type: 'donut',
        toolbar: {
            show: false,
        },
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
                        label: 'Total',
                        fontSize: '18px',
                        fontWeight: 400,
                        color: '#495057',
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

/* project overview chart */
var options3 = {
    series: [{
        name: 'On Progress',
        data: [25, 45, 41, 67, 22, 43, 44]
    }, {
        name: 'Pending',
        data: [35, 23, 20, 8, 13, 27, 13]
    }, {
        name: 'COmpleted',
        data: [40, 17, 15, 15, 21, 14, 11]
    }],
    chart: {
        type: 'bar',
        height: 315,
        stacked: true,
        toolbar: {
            show: true
        },
        zoom: {
            enabled: true
        },
        toolbar: {
            show: false,
        },
    },
    grid: {
        borderColor: '#f1f1f1',
        strokeDashArray: 3
    },
    responsive: [{
        breakpoint: 480,
        options: {
            legend: {
                position: 'bottom',
                offsetX: -10,
                offsetY: 0
            }
        }
    }],
    colors: ["rgba(51, 102, 255, 1)", "rgba(254, 127, 0, 0.5)", "rgba(51, 102, 255, 0.2)"],
    legend: {
        show: false,
        position: 'top'
    },
    plotOptions: {
        bar: {
            columnWidth: "15%",
			borderRadius: 2,
        }
    },
    dataLabels: {
        enabled: false
    },
    xaxis: {
        categories: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
		labels: {
            rotate: -90
        }
    },
    fill: {
        opacity: 1
    }
};
document.getElementById('project-overview').innerHTML = '';
var chart3 = new ApexCharts(document.querySelector("#project-overview"), options3);
chart3.render();
function projectOverview() {
    chart3.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(254, 127, 0, 1)", "rgba(" + myVarVal + ", 0.2)"],
    })
} 
/* project overview chart */ 

(function () {
    "use strict";
    /* To choose date */
    flatpickr("#date", {});

    
    /* For Time Picker */
    flatpickr("#timepikcr", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
    });

	// vertical swiper
    var swiper = new Swiper(".upcoming-events-swiper", {
        direction: "vertical",
		slidesPerView: 2,
        // spaceBetween: 5,
        pagination: {
            el: ".swiper-pagination",
            clickable: true,
        },
        loop: true,
        autoplay: {
            delay: 1500,
            disableOnInteraction: false
        }
    });
    
})();
