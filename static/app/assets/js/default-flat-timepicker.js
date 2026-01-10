// Time Picker
const timepickerElements = document.querySelectorAll('.time-picker');

timepickerElements.forEach((timepickerElement) => {
    flatpickr(timepickerElement, {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
    });
});
// Time Picker