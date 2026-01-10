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
        height: 310,
        toolbar: {
            show: false,
        }
    },
    grid: {
        borderColor: '#f1f1f1',
        strokeDashArray: 3
    },
    colors: [ "#e4e7ed", "rgb(51, 102, 255)"],
    plotOptions: {
        bar: {
            colors: {
                ranges: [{
                    from: -100,
                    to: -46,
                    color: '#ebeff5'
                }, {
                    from: -45,
                    to: 0,
                    color: '#ebeff5'
                }]
            },
            columnWidth: '40%',
            borderRadius: 6,
        }
    },
    dataLabels: {
        enabled: false,
    },
    stroke: {
        show: true,
        width: 2,
        colors: undefined,
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
document.getElementById('chartline1').innerHTML = '';
var chart1 = new ApexCharts(document.querySelector("#chartline1"), options1);
chart1.render();

function chartline1() {
    chart1.updateOptions({
        colors: ["rgba(" + myVarVal + ", 0.2)", "rgba(" + myVarVal + ", 1)"],
    });
}
/* Profits Earned Chart */