/* project overview chart */
var options = {
    series: [{
        name: 'On Progress',
        data: [25, 45, 41, 67, 22, 43, 44, 45, 41, 67, 22, 43]
    }, {
        name: 'Pending',
        data: [35, 23, 20, 8, 13, 27, 13, 23, 20, 8, 13, 27]
    }, {
        name: 'COmpleted',
        data: [40, 17, 15, 15, 21, 14, 11, 17, 15, 15, 21, 14]
    }],
    chart: {
        type: 'bar',
        height: 315,
        stacked: true,
        toolbar: {
            show: false
        },
        zoom: {
            enabled: true
        }
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
            columnWidth: "18%",
			borderRadius: 2,
        }
    },
    dataLabels: {
        enabled: false
    },
    xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
		labels: {
            rotate: -90
        }
    },
    fill: {
        opacity: 1
    }
};
document.getElementById('ticketoverview').innerHTML = '';
var chart3 = new ApexCharts(document.querySelector("#ticketoverview"), options);
chart3.render();
function ticketoverview() {
    chart3.updateOptions({
        colors: ["rgba(" + myVarVal + ", 1)", "rgba(254, 127, 0, 1)", "rgba(" + myVarVal + ", 0.2)"],
    })
} 
/* project overview chart */ 