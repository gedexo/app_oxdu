/* attendance-details2 chart*/
var options = {
    chart: {
        height: 140,
        type: "radialBar",
    },

    series: [100],
    colors: ["rgba(13,205,148,1)"],
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 0,
                size: "65%",
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
    labels: ['09:00 hrs'],
};
document.querySelector("#attendance-details2").innerHTML = ""
var chart = new ApexCharts(document.querySelector("#attendance-details2"), options);
chart.render();
/* attendance-details2 chart*/
(function () {
    "use strict";
    /* To choose date */
    // flatpickr("#date", {});

    
    /* For Time Picker */
    flatpickr("#timepikcr", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
    });
})();