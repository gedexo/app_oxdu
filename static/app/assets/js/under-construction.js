
function updateTimer() {
    future = Date.parse("Dec 19, 2023 11:30:00");
    now = new Date();
    diff = future - now;

    days = Math.floor(diff / (1000 * 60 * 60 * 24));
    hours = Math.floor(diff / (1000 * 60 * 60));
    mins = Math.floor(diff / (1000 * 60));
    secs = Math.floor(diff / 1000);

    d = days;
    h = hours - days * 24;
    m = mins - hours * 60;
    s = secs - mins * 60;

    document.getElementById("countdown-timer")
        .innerHTML =
        '<div class="col-xxl-2 col-xl-3 col-lg-3 col-md-3 col-sm-3 col-12"><div class="under-maintenance-time rounded-circle"><h2 class="fw-semibold text-fixed-white mb-0">' + d + '</h2><p class="mb-0 fs-12 text-fixed-white">Days</p></div></div>' +
        '<div class="col-xxl-2 col-xl-3 col-lg-3 col-md-3 col-sm-3 col-12"><div class="under-maintenance-time rounded-circle"><h2 class="fw-semibold text-fixed-white mb-0">' + h + '</h2><p class="mb-0 fs-12 text-fixed-white">Hours</p></div></div>' +
        '<div class="col-xxl-2 col-xl-3 col-lg-3 col-md-3 col-sm-3 col-12"><div class="under-maintenance-time rounded-circle"><h2 class="fw-semibold text-fixed-white mb-0">' + m + '</h2><p class="mb-0 fs-12 text-fixed-white">Minutes</p></div></div>' +
        '<div class="col-xxl-2 col-xl-3 col-lg-3 col-md-3 col-sm-3 col-12"><div class="under-maintenance-time rounded-circle"><h2 class="fw-semibold text-fixed-white mb-0">' + s + '</h2><p class="mb-0 fs-12 text-fixed-white">Seconds</p></div></div>'
}
setInterval('updateTimer()', 1000);