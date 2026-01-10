/* leaves overview */
var options = {
    series: [14, 8, 20, 18],
    labels: ["Casual Leaves","Sick Leaves", "Gifted Leaves", "Remaining Leaves"],
    chart: {
        height: 290,
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

(function () {
    "use strict"

    /* calendar3 */
    var calendarEl = document.getElementById('leave-calendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      headerToolbar: {
        left: 'prev',
        center: 'title',
        right: 'next'
      },
      defaultView: 'month',
      navLinks: true, // can click day/week names to navigate views
      businessHours: true, // display business hours
      editable: true,
      selectable: true,
      selectMirror: true,
      droppable: true, // this allows things to be dropped onto the calendar
  
      select: function (arg) {
        var title = prompt('Event Title:');
        if (title) {
          calendar.addEvent({
            title: title,
            start: arg.start,
            end: arg.end,
            allDay: arg.allDay
          })
        }
        calendar.unselect()
      },
    //   eventClick: function (arg) {
    //     if (confirm('Are you sure you want to delete this event?')) {
    //       arg.event.remove()
    //     }
    //   },
  
      editable: true,
      dayMaxEvents: true, // allow "more" link when too many events
    //   eventSources: [sptCalendarEvents, sptBirthdayEvents, sptHolidayEvents, sptOtherEvents,],
  
    });
    calendar.render();

})();