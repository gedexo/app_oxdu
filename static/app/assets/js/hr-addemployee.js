/* attendance chart*/
var options = {
    chart: {
        height: 127,
        width: 100,
        type: "radialBar",
    },

    series: [0],
    colors: ["rgba(51,102,255,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "55%",
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
    labels: ["Status"]
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

    series: [0],
    colors: ["rgba(254,127,0,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "55%",
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
    labels: ["Status"]
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

    series: [0],
    colors: ["rgba(13,205,148,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "55%",
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
    labels: ["Status"]
};
document.querySelector("#performance").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#performance"), options);
chart.render();
/* performance chart*/