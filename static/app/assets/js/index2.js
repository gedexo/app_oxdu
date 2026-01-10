/* slary attendance Chart */
var options = {
    series: [{
        name: "Earnings",
        data: [80, 60, 50, 30, 65, 35, 64, 51, 59, 80, 70, 78]
    }, {
        name: "Students",
        data: [85, 65, 55, 37, 60, 32, 47, 31, 54, 70, 60, 62]
    }],
    chart: {
        height: 370,
        type: "bar",
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: [1, 1],
        show: true,
        curve: ['smooth', 'smooth'],
    },
    grid: {
        borderColor: '#f3f3f3',
        strokeDashArray: 3
    },
    xaxis: {
        axisBorder: {
            color: 'rgba(119, 119, 142, 0.05)',
        },
    },
    legend: {
        show: false
    },
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    markers: {
        size: 0
    },
    colors: ["rgba(51, 102, 255, 0.2)", "rgb(51, 102, 255)"],
    plotOptions: {
        bar: {
            columnWidth: "35%",
            borderRadius: 6,
            borderRadiusApplication: 'end',
        }
    },
};
document.getElementById('salary-attendance-chart').innerHTML = ''
var chart1 = new ApexCharts(document.querySelector("#salary-attendance-chart"), options);
chart1.render();

function salaryAttendance() {
	chart1.updateOptions({
		colors: ["rgba(" + myVarVal + ", 0.2)", "rgb(" + myVarVal + ")"],
	})
}
/* slary attendance Chart */

(function () {
    "use strict"

    /* calendar3 */
    var calendarEl = document.getElementById('calendar3');
  
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
